/**
 * Service Worker для ГКУ ОП Заявки
 * 
 * Обеспечивает:
 * - Кэширование статических ресурсов (CSS, JS, изображения)
 * - Перехват сетевых запросов для работы в офлайн-режиме
 * - Стратегии кэширования (Cache First для статики, Network First для API)
 * - Уведомление клиента о статусе соединения
 * - Фоновую синхронизацию при восстановлении соединения
 */

const CACHE_NAME = 'gkuop-cache-v2';
const STATIC_CACHE = 'gkuop-static-v2';
const API_CACHE = 'gkuop-api-v2';
const IMAGE_CACHE = 'gkuop-images-v2';

// Ресурсы для предварительного кэширования при установке
const PRECACHE_URLS = [
    '/',
    '/static/css/main.css',
    '/static/js/auth.js',
    '/static/js/pwa.js',
    '/static/favicon.ico',
    '/manifest.json',
];

// Стратегии кэширования по типам ресурсов
const ROUTE_STRATEGIES = {
    // Статические ресурсы — Cache First
    static: {
        patterns: [
            /\/static\/.*/,
            /\/manifest\.json$/,
            /\/favicon\.ico$/,
        ],
        strategy: 'cache-first',
    },
    // API-запросы — только Network (без кэширования).
    // Офлайн-режим для API реализован через IndexedDB в pwa.js.
    api: {
        patterns: [
            /\/api\/tickets(\/.*)?$/,
            /\/api\/offices$/,
            /\/api\/statuses$/,
            /\/api\/statistics$/,
            /\/api\/tasks(\/.*)?$/,
            /\/api\/pwa\/.*$/,
        ],
        strategy: 'network-only',
    },
    // Изображения — Cache First
    images: {
        patterns: [
            /\/api\/images\/\d+\/(download|thumbnail)/,
            /\/uploads\/.*/,
        ],
        strategy: 'cache-first',
    },
};

// ─── События жизненного цикла Service Worker ────────────────────

self.addEventListener('install', (event) => {
    console.log('[SW] Установка...');

    // Предварительное кэширование статических ресурсов
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                return cache.addAll(PRECACHE_URLS);
            })
            .then(() => {
                console.log('[SW] Предварительное кэширование завершено');
                // Активируем SW сразу, не ждём закрытия страницы
                return self.skipWaiting();
            })
            .catch((err) => {
                console.error('[SW] Ошибка предварительного кэширования:', err);
            })
    );
});

self.addEventListener('activate', (event) => {
    console.log('[SW] Активация...');

    // Очистка старых кэшей
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                const validCaches = [CACHE_NAME, STATIC_CACHE, API_CACHE, IMAGE_CACHE];
                return Promise.all(
                    cacheNames
                        .filter((name) => !validCaches.includes(name))
                        .map((name) => {
                            console.log('[SW] Удаление старого кэша:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[SW] Активирован');
                // Начинаем управлять всеми клиентами
                return self.clients.claim();
            })
    );
});

// ─── Обработка fetch-запросов ───────────────────────────────────

self.addEventListener('fetch', (event) => {
    const request = event.request;

    // Пропускаем навигационные запросы (переходы по страницам) — они не кэшируются
    if (request.mode === 'navigate') {
        return;
    }

    // Пропускаем не-GET запросы — они не кэшируются и отправляются напрямую на сервер
    if (request.method !== 'GET') {
        return;
    }

    // Определяем стратегию для запроса
    const strategy = getStrategy(request.url);

    switch (strategy) {
        case 'cache-first':
            event.respondWith(cacheFirst(request));
            break;
        case 'network-first':
            event.respondWith(networkFirst(request));
            break;
        case 'network-only':
            // API-запросы не кэшируются, только сеть
            // Не вызываем event.respondWith — браузер отправит запрос напрямую
            return;
        default:
            // По умолчанию — Network First
            event.respondWith(networkFirst(request));
    }
});

/**
 * Определение стратегии кэширования для URL.
 * @param {string} url
 * @returns {string} 'cache-first' | 'network-first' | 'network-only'
 */
function getStrategy(url) {
    for (const [, config] of Object.entries(ROUTE_STRATEGIES)) {
        for (const pattern of config.patterns) {
            if (pattern.test(url)) {
                return config.strategy;
            }
        }
    }
    return 'network-first';
}

/**
 * Стратегия Cache First.
 * Сначала проверяем кэш, если нет — запрашиваем с сети.
 * Для статики таймаут короткий (5с), так как ресурс критичен для отображения.
 * @param {Request} request
 * @returns {Promise<Response>}
 */
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    // Для статических ресурсов таймаут короче — 5 секунд
    const TIMEOUT_MS = request.url.includes('/static/') ? 5000 : 25000;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
        const networkResponse = await fetch(request, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (networkResponse && networkResponse.ok) {
            const cache = await caches.open(getCacheName(request.url));
            // Кэшируем только успешные ответы
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        clearTimeout(timeoutId);
        // Если нет сети и нет кэша — возвращаем офлайн-страницу
        console.error('[SW] Ошибка загрузки (Cache First):', request.url, error);
        return new Response(
            JSON.stringify({ error: 'Нет соединения с сервером', offline: true }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' },
            }
        );
    }
}

/**
 * Стратегия Network First.
 * Сначала пробуем загрузить с сети, при ошибке — из кэша.
 * @param {Request} request
 * @returns {Promise<Response>}
 */
async function networkFirst(request) {
    const TIMEOUT_MS = 25000; // 25 секунд таймаут для сети
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
        const networkResponse = await fetch(request, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (networkResponse && networkResponse.ok) {
            const cache = await caches.open(getCacheName(request.url));
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        clearTimeout(timeoutId);
        console.log('[SW] Сеть недоступна или таймаут, используем кэш для:', request.url);

        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Для API-запросов возвращаем JSON с ошибкой
        if (request.url.includes('/api/')) {
            return new Response(
                JSON.stringify({
                    error: 'Нет соединения с сервером',
                    offline: true,
                    cached: false,
                }),
                {
                    status: 503,
                    headers: { 'Content-Type': 'application/json' },
                }
            );
        }

        // Для страниц возвращаем заглушку
        return new Response(
            '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Нет соединения</title>' +
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">' +
            '<style>body{font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background:#f0f2f5}' +
            '.offline-card{text-align:center;padding:40px;background:white;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}' +
            '.offline-icon{font-size:64px;margin-bottom:20px}' +
            'h1{color:#1a1a2e;margin-bottom:10px}' +
            'p{color:#6b7280;margin-bottom:20px}' +
            '.retry-btn{padding:12px 24px;background:#e94560;color:white;border:none;border-radius:6px;cursor:pointer;font-size:16px}' +
            '.retry-btn:hover{background:#d63851}</style></head><body>' +
            '<div class="offline-card">' +
            '<div class="offline-icon">📡</div>' +
            '<h1>Нет соединения</h1>' +
            '<p>Проверьте подключение к интернету.<br>Изменения сохраняются локально и будут синхронизированы при восстановлении связи.</p>' +
            '<button class="retry-btn" onclick="location.reload()">Повторить</button>' +
            '</div></body></html>',
            {
                status: 503,
                headers: { 'Content-Type': 'text/html; charset=utf-8' },
            }
        );
    }
}

/**
 * Определение имени кэша для URL.
 * @param {string} url
 * @returns {string}
 */
function getCacheName(url) {
    if (url.includes('/static/') || url.includes('/manifest.json') || url.includes('/favicon.ico')) {
        return STATIC_CACHE;
    }
    if (url.includes('/api/images/') || url.includes('/uploads/')) {
        return IMAGE_CACHE;
    }
    if (url.includes('/api/')) {
        return API_CACHE;
    }
    return CACHE_NAME;
}

// ─── Обработка сообщений от клиента ─────────────────────────────

self.addEventListener('message', (event) => {
    const data = event.data;

    if (!data) return;

    switch (data.type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;

        case 'CLEAR_CACHE':
            // Очистка всех кэшей
            event.waitUntil(
                caches.keys().then((cacheNames) => {
                    return Promise.all(
                        cacheNames.map((name) => caches.delete(name))
                    );
                })
            );
            break;

        case 'UPDATE_CACHE':
            // Обновление кэша для указанного URL
            if (data.url) {
                event.waitUntil(updateCache(data.url));
            }
            break;

        default:
            console.log('[SW] Получено сообщение:', data.type);
    }
});

/**
 * Обновление кэша для конкретного URL.
 * @param {string} url
 */
async function updateCache(url) {
    try {
        const response = await fetch(url);
        if (response.ok) {
            const cache = await caches.open(getCacheName(url));
            await cache.put(url, response);
            console.log('[SW] Кэш обновлён:', url);
        }
    } catch (error) {
        console.error('[SW] Ошибка обновления кэша:', url, error);
    }
}

// ─── Фоновая синхронизация ─────────────────────────────────────

self.addEventListener('sync', (event) => {
    console.log('[SW] Событие sync:', event.tag);

    if (event.tag === 'sync-tickets') {
        event.waitUntil(syncTickets());
    }
});

/**
 * Фоновая синхронизация заявок.
 * Уведомляет клиент о необходимости синхронизации.
 */
async function syncTickets() {
    try {
        const clients = await self.clients.matchAll();
        clients.forEach((client) => {
            client.postMessage({
                type: 'SYNC_STATUS',
                status: 'triggered',
                message: 'Фоновая синхронизация запущена',
            });
        });
    } catch (error) {
        console.error('[SW] Ошибка фоновой синхронизации:', error);
    }
}

// ─── Обработка push-уведомлений (для будущего использования) ────

self.addEventListener('push', (event) => {
    if (!event.data) return;

    try {
        const data = event.data.json();
        const title = data.title || 'ГКУ ОП Заявки';
        const options = {
            body: data.body || '',
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico',
            data: data.data || {},
        };

        event.waitUntil(
            self.registration.showNotification(title, options)
        );
    } catch (error) {
        console.error('[SW] Ошибка обработки push:', error);
    }
});

self.addEventListener('notificationclick', (event) => {
    const notification = event.notification;
    notification.close();

    // Открываем страницу заявки, если есть ticket_number
    const ticketNumber = notification.data && notification.data.ticket_number;
    const url = ticketNumber ? `/tickets/${ticketNumber}` : '/';

    event.waitUntil(
        clients.openWindow(url)
    );
});
