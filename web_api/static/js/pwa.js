/**
 * PWA Module — прогрессивное веб-приложение
 * 
 * Предоставляет:
 * - Регистрацию Service Worker
 * - Генерацию UUID v4 на клиенте
 * - Локальную базу данных IndexedDB через Dexie.js
 * - Автоматическую синхронизацию с сервером при восстановлении соединения
 * - UI-индикаторы статуса синхронизации
 * 
 * Зависимости: Dexie.js (загружается через CDN)
 */

// ─── UUID v4 генератор ──────────────────────────────────────────

const UUID = {
    /**
     * Генерирует UUID версии 4 (случайный).
     * Использует crypto.randomUUID() если доступен, иначе fallback.
     * @returns {string} UUID v4
     */
    v4() {
        if (typeof crypto !== 'undefined' && crypto.randomUUID) {
            return crypto.randomUUID();
        }
        // Fallback для старых браузеров
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
            const r = (Math.random() * 16) | 0;
            const v = c === 'x' ? r : (r & 0x3) | 0x8;
            return v.toString(16);
        });
    },

    /**
     * Проверяет, является ли строка валидным UUID v4.
     * @param {string} str
     * @returns {boolean}
     */
    isValid(str) {
        return /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(str);
    }
};


// ─── Dexie.js база данных для локального хранения ───────────────

const LocalDB = {
    _db: null,
    _ready: false,

    /** Инициализация локальной базы данных */
    async init() {
        if (this._ready) return;

        // Загружаем Dexie, если ещё не загружен
        if (typeof Dexie === 'undefined') {
            await this._loadDexie();
        }

        this._db = new Dexie('GKUOP_LocalDB');

        // Определяем схему базы данных
        this._db.version(1).stores({
            // Локальные заявки (созданные/изменённые офлайн)
            tickets: 'uuid, ticket_number, status, updated_at, synced_at, sync_status',
            // Очередь синхронизации
            sync_queue: '++id, uuid, action, ticket_uuid, created_at, retry_count',
            // Кэш заявок с сервера для офлайн-доступа
            tickets_cache: 'ticket_number, status, updated_at',
            // Метаданные синхронизации
            sync_meta: 'key',
        });

        this._ready = true;
        console.log('[PWA] LocalDB инициализирована');
    },

    /** Загрузка Dexie.js с CDN (с fallback на локальную копию) */
    async _loadDexie() {
        return new Promise((resolve, reject) => {
            if (typeof Dexie !== 'undefined') {
                resolve();
                return;
            }

            const tryLoad = (src) => {
                return new Promise((res, rej) => {
                    const script = document.createElement('script');
                    script.src = src;
                    script.crossOrigin = 'anonymous';
                    script.onload = () => res();
                    script.onerror = () => rej(new Error(`Failed to load: ${src}`));
                    document.head.appendChild(script);
                });
            };

            // Пробуем CDN, при ошибке — локальную копию
            tryLoad('https://unpkg.com/dexie@3.2.6/dist/dexie.min.js')
                .then(() => resolve())
                .catch(() => {
                    console.warn('[PWA] CDN Dexie.js недоступен, пробуем локальную копию');
                    tryLoad('/static/js/dexie.min.js')
                        .then(() => resolve())
                        .catch(() => {
                            console.error('[PWA] Не удалось загрузить Dexie.js (CDN + локальный fallback)');
                            reject(new Error('Failed to load Dexie.js'));
                        });
                });
        });
    },

    /**
     * Сохранить заявку в локальную базу (создание или обновление).
     * @param {object} ticketData - данные заявки
     * @param {string} [ticketData.uuid] - UUID (генерируется автоматически если нет)
     * @returns {Promise<object>} сохранённая заявка
     */
    async saveTicket(ticketData) {
        await this.init();
        const now = new Date().toISOString();
        const ticket = {
            ...ticketData,
            uuid: ticketData.uuid || UUID.v4(),
            updated_at: now,
            sync_status: ticketData.sync_status || 'pending', // pending | synced | conflict
        };

        // Если заявка новая и нет номера, генерируем временный
        if (!ticket.ticket_number) {
            ticket.ticket_number = `TEMP-${ticket.uuid.slice(0, 8)}`;
        }

        await this._db.tickets.put(ticket);

        // Добавляем в очередь синхронизации
        await this.addToSyncQueue({
            uuid: ticket.uuid,
            action: ticketData._existing ? 'update' : 'create',
            ticket_uuid: ticket.uuid,
            data: ticket,
        });

        return ticket;
    },

    /**
     * Получить заявку по UUID.
     * @param {string} uuid
     * @returns {Promise<object|null>}
     */
    async getTicket(uuid) {
        await this.init();
        return this._db.tickets.get(uuid);
    },

    /**
     * Получить все локальные заявки с статусом синхронизации.
     * @param {string} [syncStatus] - фильтр по статусу ('pending', 'synced', 'conflict')
     * @returns {Promise<Array>}
     */
    async getLocalTickets(syncStatus = null) {
        await this.init();
        if (syncStatus) {
            return this._db.tickets.where('sync_status').equals(syncStatus).toArray();
        }
        return this._db.tickets.toArray();
    },

    /**
     * Кэшировать заявку с сервера для офлайн-доступа.
     * @param {object} ticket - данные заявки с сервера
     */
    async cacheTicket(ticket) {
        await this.init();
        const cacheData = {
            ...ticket,
            cached_at: new Date().toISOString(),
        };
        await this._db.tickets_cache.put(cacheData);
    },

    /**
     * Кэшировать список заявок с сервера.
     * @param {Array} tickets - массив заявок
     */
    async cacheTickets(tickets) {
        await this.init();
        const tx = this._db.transaction('rw', this._db.tickets_cache, async () => {
            for (const ticket of tickets) {
                await this._db.tickets_cache.put({
                    ...ticket,
                    cached_at: new Date().toISOString(),
                });
            }
        });
        return tx;
    },

    /**
     * Получить кэшированные заявки (для офлайн-режима).
     * @param {object} [filters] - фильтры
     * @returns {Promise<Array>}
     */
    async getCachedTickets(filters = {}) {
        await this.init();
        let collection = this._db.tickets_cache.toCollection();

        if (filters.status) {
            collection = this._db.tickets_cache.where('status').equals(filters.status);
        }

        let results = await collection.toArray();

        // Сортировка по updated_at (свежие сверху)
        results.sort((a, b) => {
            const dateA = a.updated_at || a.cached_at || '';
            const dateB = b.updated_at || b.cached_at || '';
            return dateB.localeCompare(dateA);
        });

        return results;
    },

    /**
     * Добавить операцию в очередь синхронизации.
     * @param {object} item - элемент очереди
     */
    async addToSyncQueue(item) {
        await this.init();
        const queueItem = {
            uuid: item.uuid || UUID.v4(),
            action: item.action, // 'create' | 'update' | 'delete'
            ticket_uuid: item.ticket_uuid,
            data: item.data || null,
            created_at: new Date().toISOString(),
            retry_count: 0,
            last_error: null,
        };
        await this._db.sync_queue.add(queueItem);
    },

    /**
     * Получить все элементы очереди синхронизации.
     * @returns {Promise<Array>}
     */
    async getSyncQueue() {
        await this.init();
        return this._db.sync_queue.orderBy('created_at').toArray();
    },

    /**
     * Удалить элемент из очереди синхронизации.
     * @param {number} id - ID элемента очереди
     */
    async removeFromSyncQueue(id) {
        await this.init();
        await this._db.sync_queue.delete(id);
    },

    /**
     * Очистить обработанные элементы очереди.
     */
    async clearProcessedQueue() {
        await this.init();
        await this._db.sync_queue.clear();
    },

    /**
     * Обновить статус синхронизации заявки.
     * @param {string} uuid - UUID заявки
     * @param {string} status - 'synced' | 'conflict' | 'pending'
     * @param {object} [serverData] - данные с сервера после синхронизации
     */
    async updateSyncStatus(uuid, status, serverData = null) {
        await this.init();
        const ticket = await this._db.tickets.get(uuid);
        if (ticket) {
            ticket.sync_status = status;
            ticket.synced_at = new Date().toISOString();
            if (serverData) {
                // Обновляем поля из ответа сервера
                Object.assign(ticket, serverData);
            }
            await this._db.tickets.put(ticket);
        }
    },

    /**
     * Получить мета-данные синхронизации.
     * @param {string} key
     * @returns {Promise<object|null>}
     */
    async getSyncMeta(key) {
        await this.init();
        return this._db.sync_meta.get(key);
    },

    /**
     * Установить мета-данные синхронизации.
     * @param {string} key
     * @param {any} value
     */
    async setSyncMeta(key, value) {
        await this.init();
        await this._db.sync_meta.put({ key, value, updated_at: new Date().toISOString() });
    },

    /**
     * Получить количество ожидающих синхронизации элементов.
     * @returns {Promise<number>}
     */
    async getPendingCount() {
        await this.init();
        return this._db.sync_queue.count();
    },

    /**
     * Очистить все локальные данные.
     */
    async clearAll() {
        await this.init();
        await this._db.tickets.clear();
        await this._db.sync_queue.clear();
        await this._db.tickets_cache.clear();
        await this._db.sync_meta.clear();
    }
};


// ─── Менеджер синхронизации ─────────────────────────────────────

const SyncManager = {
    _isSyncing: false,
    _syncInterval: null,
    _online: navigator.onLine,
    _listeners: [],
    _retryDelay: 5000, // 5 секунд между попытками
    _maxRetries: 5,

    /**
     * Инициализация менеджера синхронизации.
     * @param {object} options
     * @param {number} [options.interval=30000] - интервал проверки синхронизации (мс)
     * @param {number} [options.retryDelay=5000] - задержка между retry (мс)
     * @param {number} [options.maxRetries=5] - макс. количество retry
     */
    init(options = {}) {
        this._retryDelay = options.retryDelay || 5000;
        this._maxRetries = options.maxRetries || 5;

        // Слушаем события online/offline
        window.addEventListener('online', () => this._handleOnline());
        window.addEventListener('offline', () => this._handleOffline());

        // Проверяем соединение через регулярные промежутки
        const interval = options.interval || 30000; // 30 секунд
        this._syncInterval = setInterval(() => this._checkAndSync(), interval);

        // Немедленная проверка при инициализации
        if (navigator.onLine) {
            setTimeout(() => this._checkAndSync(), 1000);
        }

        console.log('[PWA] SyncManager инициализирован');
    },

    /**
     * Подписка на события синхронизации.
     * @param {function} callback - функция обратного вызова
     * @returns {function} функция для отписки
     */
    onSync(callback) {
        this._listeners.push(callback);
        return () => {
            this._listeners = this._listeners.filter(cb => cb !== callback);
        };
    },

    /** Уведомление слушателей */
    _notify(event, data) {
        this._listeners.forEach(cb => {
            try {
                cb(event, data);
            } catch (e) {
                console.error('[PWA] Ошибка в слушателе синхронизации:', e);
            }
        });
    },

    /** Обработчик восстановления соединения */
    async _handleOnline() {
        this._online = true;
        console.log('[PWA] Соединение восстановлено');
        this._notify('online', {});
        await this._checkAndSync();
    },

    /** Обработчик потери соединения */
    _handleOffline() {
        this._online = false;
        console.log('[PWA] Соединение потеряно');
        this._notify('offline', {});
    },

    /**
     * Проверка и запуск синхронизации.
     */
    async _checkAndSync() {
        if (this._isSyncing) return;
        if (!navigator.onLine) return;

        try {
            const pendingCount = await LocalDB.getPendingCount();
            if (pendingCount === 0) return;

            await this.sync();
        } catch (e) {
            console.error('[PWA] Ошибка при проверке синхронизации:', e);
        }
    },

    /**
     * Запуск полной синхронизации.
     * Отправляет все накопленные локальные изменения на сервер.
     */
    async sync() {
        if (this._isSyncing) {
            console.log('[PWA] Синхронизация уже выполняется');
            return;
        }

        if (!navigator.onLine) {
            console.log('[PWA] Нет соединения, синхронизация отложена');
            this._notify('error', { message: 'Нет соединения с сервером' });
            return;
        }

        this._isSyncing = true;
        this._notify('start', {});

        try {
            const queue = await LocalDB.getSyncQueue();

            if (queue.length === 0) {
                this._isSyncing = false;
                this._notify('complete', { synced: 0 });
                return;
            }

            this._notify('progress', {
                total: queue.length,
                processed: 0,
                message: `Синхронизация ${queue.length} изменений...`,
            });

            let synced = 0;
            let errors = 0;

            for (let i = 0; i < queue.length; i++) {
                const item = queue[i];

                try {
                    await this._syncItem(item);
                    await LocalDB.removeFromSyncQueue(item.id);
                    synced++;

                    this._notify('progress', {
                        total: queue.length,
                        processed: i + 1,
                        message: `Синхронизация ${i + 1} из ${queue.length}...`,
                    });
                } catch (e) {
                    errors++;
                    console.error(`[PWA] Ошибка синхронизации элемента ${item.id}:`, e);

                    // Увеличиваем счётчик retry
                    item.retry_count = (item.retry_count || 0) + 1;
                    item.last_error = e.message;

                    if (item.retry_count >= this._maxRetries) {
                        // После макс. числа попыток — помечаем как конфликт
                        console.warn(`[PWA] Элемент ${item.id} превысил лимит retry, помечаем как конфликт`);
                        await LocalDB.updateSyncStatus(item.ticket_uuid, 'conflict');
                        await LocalDB.removeFromSyncQueue(item.id);
                    } else {
                        // Обновляем в очереди
                        await LocalDB._db.sync_queue.put(item);
                    }
                }
            }

            // Обновляем мета-данные последней синхронизации
            await LocalDB.setSyncMeta('last_sync', {
                timestamp: new Date().toISOString(),
                synced,
                errors,
            });

            this._notify('complete', { synced, errors });
            console.log(`[PWA] Синхронизация завершена: ${synced} успешно, ${errors} ошибок`);
        } catch (e) {
            console.error('[PWA] Критическая ошибка синхронизации:', e);
            this._notify('error', { message: e.message });
        } finally {
            this._isSyncing = false;
        }
    },

    /**
     * Синхронизация одного элемента очереди.
     * @param {object} item - элемент очереди
     */
    async _syncItem(item) {
        const token = AUTH.getToken();
        if (!token) {
            throw new Error('Не авторизован');
        }

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        };

        let response;

        switch (item.action) {
            case 'create':
                response = await fetch('/api/pwa/tickets', {
                    method: 'POST',
                    headers,
                    body: JSON.stringify(item.data),
                });
                break;

            case 'update':
                response = await fetch(`/api/pwa/tickets/${item.data.ticket_number}`, {
                    method: 'PUT',
                    headers,
                    body: JSON.stringify(item.data),
                });
                break;

            case 'delete':
                response = await fetch(`/api/pwa/tickets/${item.data.ticket_number}`, {
                    method: 'DELETE',
                    headers,
                });
                break;

            default:
                throw new Error(`Неизвестное действие: ${item.action}`);
        }

        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const errData = await response.json();
                errorMsg = errData.message || errData.error || errorMsg;
            } catch (e) {
                // ignore
            }
            throw new Error(errorMsg);
        }

        const result = await response.json();

        // Обновляем статус синхронизации локальной заявки
        if (result.ticket || result.data) {
            const serverData = result.ticket || result.data;
            await LocalDB.updateSyncStatus(item.ticket_uuid, 'synced', serverData);
        } else {
            await LocalDB.updateSyncStatus(item.ticket_uuid, 'synced');
        }
    },

    /**
     * Принудительный запуск синхронизации.
     */
    async forceSync() {
        return this.sync();
    },

    /**
     * Проверка статуса соединения.
     * @returns {boolean}
     */
    isOnline() {
        return navigator.onLine;
    },

    /**
     * Проверка, выполняется ли синхронизация.
     * @returns {boolean}
     */
    isSyncing() {
        return this._isSyncing;
    },

    /**
     * Остановка менеджера синхронизации.
     */
    destroy() {
        if (this._syncInterval) {
            clearInterval(this._syncInterval);
            this._syncInterval = null;
        }
        this._listeners = [];
    }
};


// ─── UI-компонент статуса синхронизации ─────────────────────────

const SyncUI = {
    _container: null,
    _badge: null,
    _indicator: null,
    _initialized: false,

    /**
     * Инициализация UI-элементов статуса синхронизации.
     */
    init() {
        if (this._initialized) return;
        this._initialized = true;

        // Создаём контейнер для индикатора синхронизации
        this._createElements();

        // Подписываемся на события синхронизации
        SyncManager.onSync((event, data) => this._handleSyncEvent(event, data));

        // Слушаем online/offline
        window.addEventListener('online', () => this._updateOnlineStatus(true));
        window.addEventListener('offline', () => this._updateOnlineStatus(false));

        // Начальное состояние
        this._updateOnlineStatus(navigator.onLine);

        console.log('[PWA] SyncUI инициализирован');
    },

    /** Создание DOM-элементов */
    _createElements() {
        // Индикатор в хедере
        const headerRight = document.getElementById('authIndicator');
        if (!headerRight) return;

        this._indicator = document.createElement('div');
        this._indicator.className = 'pwa-status';
        this._indicator.innerHTML = `
            <span class="pwa-status-dot" id="pwaStatusDot"></span>
            <span class="pwa-status-text" id="pwaStatusText">В сети</span>
        `;
        this._indicator.title = 'Статус соединения';

        // Вставляем перед кнопкой гамбургера
        const hamburgerBtn = document.getElementById('hamburgerBtn');
        if (hamburgerBtn) {
            headerRight.insertBefore(this._indicator, hamburgerBtn);
        } else {
            headerRight.appendChild(this._indicator);
        }

        // Бейдж с количеством ожидающих синхронизации
        this._badge = document.createElement('span');
        this._badge.className = 'pwa-sync-badge';
        this._badge.style.display = 'none';
        this._indicator.appendChild(this._badge);

        // Контейнер для тостов синхронизации
        this._container = document.createElement('div');
        this._container.className = 'pwa-toast-container';
        document.body.appendChild(this._container);
    },

    /** Обработка событий синхронизации */
    _handleSyncEvent(event, data) {
        switch (event) {
            case 'start':
                this._showSyncing();
                break;

            case 'progress':
                this._updateProgress(data);
                break;

            case 'complete':
                this._showComplete(data);
                this._updateBadge(0);
                break;

            case 'error':
                this._showError(data);
                break;

            case 'online':
                this._updateOnlineStatus(true);
                break;

            case 'offline':
                this._updateOnlineStatus(false);
                break;
        }
    },

    /** Обновление статуса соединения */
    _updateOnlineStatus(online) {
        const dot = document.getElementById('pwaStatusDot');
        const text = document.getElementById('pwaStatusText');
        if (!dot || !text) return;

        if (online) {
            dot.className = 'pwa-status-dot pwa-status-online';
            text.textContent = 'В сети';
            this._indicator.title = 'Соединение активно';
        } else {
            dot.className = 'pwa-status-dot pwa-status-offline';
            text.textContent = 'Офлайн';
            this._indicator.title = 'Нет соединения — изменения сохраняются локально';
        }
    },

    /** Показ индикатора синхронизации */
    _showSyncing() {
        const dot = document.getElementById('pwaStatusDot');
        const text = document.getElementById('pwaStatusText');
        if (dot) dot.className = 'pwa-status-dot pwa-status-syncing';
        if (text) text.textContent = 'Синхронизация...';
        if (this._indicator) this._indicator.title = 'Выполняется синхронизация с сервером';
    },

    /** Обновление прогресса */
    _updateProgress(data) {
        const text = document.getElementById('pwaStatusText');
        if (text) {
            text.textContent = data.message || `Синхронизация ${data.processed}/${data.total}...`;
        }
    },

    /** Показ завершения синхронизации */
    _showComplete(data) {
        const dot = document.getElementById('pwaStatusDot');
        const text = document.getElementById('pwaStatusText');

        if (data.errors && data.errors > 0) {
            if (dot) dot.className = 'pwa-status-dot pwa-status-warning';
            if (text) text.textContent = `Синхронизировано: ${data.synced}, ошибок: ${data.errors}`;
            this._showToast(`Синхронизация завершена с ошибками (${data.errors})`, 'warning');
        } else {
            if (dot) dot.className = 'pwa-status-dot pwa-status-online';
            if (text) text.textContent = 'В сети';
            if (data.synced > 0) {
                this._showToast(`Синхронизировано ${data.synced} изменений`, 'success');
            }
        }

        // Возвращаем обычный статус через 3 секунды
        setTimeout(() => {
            this._updateOnlineStatus(navigator.onLine);
        }, 3000);
    },

    /** Показ ошибки */
    _showError(data) {
        const dot = document.getElementById('pwaStatusDot');
        const text = document.getElementById('pwaStatusText');
        if (dot) dot.className = 'pwa-status-dot pwa-status-error';
        if (text) text.textContent = 'Ошибка синхронизации';
        this._showToast(data.message || 'Ошибка синхронизации', 'error');

        setTimeout(() => {
            this._updateOnlineStatus(navigator.onLine);
        }, 5000);
    },

    /** Обновление бейджа */
    async _updateBadge(count) {
        if (!this._badge) return;
        if (count > 0) {
            this._badge.textContent = count > 99 ? '99+' : count;
            this._badge.style.display = '';
        } else {
            this._badge.style.display = 'none';
        }
    },

    /**
     * Показ тост-уведомления.
     * @param {string} message
     * @param {string} type - 'success' | 'error' | 'warning' | 'info'
     */
    _showToast(message, type = 'info') {
        if (!this._container) return;

        const toast = document.createElement('div');
        toast.className = `pwa-toast pwa-toast-${type}`;
        toast.textContent = message;

        this._container.appendChild(toast);

        // Анимация появления
        requestAnimationFrame(() => {
            toast.classList.add('pwa-toast-show');
        });

        // Авто-удаление через 5 секунд
        setTimeout(() => {
            toast.classList.remove('pwa-toast-show');
            toast.classList.add('pwa-toast-hide');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 5000);
    },

    /**
     * Обновить бейдж с количеством ожидающих элементов.
     */
    async refreshBadge() {
        try {
            const count = await LocalDB.getPendingCount();
            this._updateBadge(count);
        } catch (e) {
            console.error('[PWA] Ошибка обновления бейджа:', e);
        }
    }
};


// ─── Инициализация PWA ──────────────────────────────────────────

const PWA = {
    _initialized: false,

    /**
     * Полная инициализация PWA-модуля.
     * @param {object} [options]
     * @param {number} [options.syncInterval=30000]
     */
    async init(options = {}) {
        if (this._initialized) return;
        this._initialized = true;

        console.log('[PWA] Инициализация...');

        // 1. Регистрируем Service Worker
        await this._registerSW();

        // 2. Инициализируем локальную базу данных
        await LocalDB.init();

        // 3. Инициализируем менеджер синхронизации
        SyncManager.init({
            interval: options.syncInterval || 30000,
        });

        // 4. Инициализируем UI
        SyncUI.init();

        // 5. Обновляем бейдж с количеством ожидающих
        await SyncUI.refreshBadge();

        // 6. Периодическое обновление бейджа
        setInterval(() => SyncUI.refreshBadge(), 10000);

        console.log('[PWA] Инициализация завершена');
    },

    /** Регистрация Service Worker */
    async _registerSW() {
        if (!('serviceWorker' in navigator)) {
            console.warn('[PWA] Service Worker не поддерживается браузером');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.register('/static/js/sw.js', {
                scope: '/',
            });

            console.log('[PWA] Service Worker зарегистрирован:', registration.scope);

            // Обработка обновлений Service Worker
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                console.log('[PWA] Обновление Service Worker...');

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        // Новый SW установлен — показываем уведомление
                        SyncUI._showToast(
                            'Доступна новая версия приложения. Обновите страницу.',
                            'info'
                        );
                    }
                });
            });

            // Обработка сообщений от Service Worker
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data && event.data.type === 'SYNC_STATUS') {
                    console.log('[PWA] Сообщение от SW:', event.data);
                }
            });

            return registration;
        } catch (e) {
            console.error('[PWA] Ошибка регистрации Service Worker:', e);
        }
    },

    /**
     * Создать заявку в офлайн-режиме.
     * @param {object} ticketData - данные заявки
     * @returns {Promise<object>}
     */
    async createTicket(ticketData) {
        // Генерируем UUID для новой заявки
        const uuid = UUID.v4();
        const ticket = {
            ...ticketData,
            uuid,
            created_at: new Date().toISOString(),
            sync_status: 'pending',
        };

        // Сохраняем локально
        const saved = await LocalDB.saveTicket(ticket);

        // Пытаемся синхронизировать сразу, если есть соединение
        if (navigator.onLine) {
            SyncManager.sync().catch((e) => {
                console.warn('[PWA] Фоновая синхронизация не удалась:', e);
            });
        }

        return saved;
    },

    /**
     * Обновить заявку в офлайн-режиме.
     * @param {string} ticketNumber - номер заявки
     * @param {object} updates - обновлённые поля
     * @returns {Promise<object>}
     */
    async updateTicket(ticketNumber, updates) {
        const ticket = {
            ...updates,
            ticket_number: ticketNumber,
            _existing: true,
            updated_at: new Date().toISOString(),
            sync_status: 'pending',
        };

        const saved = await LocalDB.saveTicket(ticket);

        if (navigator.onLine) {
            SyncManager.sync().catch((e) => {
                console.warn('[PWA] Фоновая синхронизация обновления не удалась:', e);
            });
        }

        return saved;
    },

    /**
     * Получить заявки (сначала из кэша, потом с сервера).
     * @param {object} [filters]
     * @returns {Promise<Array>}
     */
    async getTickets(filters = {}) {
        // Если онлайн — пробуем получить с сервера
        if (navigator.onLine) {
            try {
                const token = AUTH.getToken();
                const headers = {};
                if (token) headers['Authorization'] = `Bearer ${token}`;

                const response = await fetch('/api/tickets', { headers });
                if (response.ok) {
                    const data = await response.json();
                    // Кэшируем полученные данные
                    if (data.tickets) {
                        await LocalDB.cacheTickets(data.tickets);
                    }
                    return data;
                }
            } catch (e) {
                console.warn('[PWA] Не удалось получить данные с сервера, используем кэш:', e);
            }
        }

        // Офлайн или ошибка — возвращаем кэш
        const cached = await LocalDB.getCachedTickets(filters);
        return { tickets: cached };
    }
};


// ─── Авто-инициализация при загрузке страницы ───────────────────

document.addEventListener('DOMContentLoaded', () => {
    // Инициализируем PWA после авторизации
    const checkAuthAndInit = () => {
        if (typeof AUTH !== 'undefined' && AUTH.isAuthenticated()) {
            PWA.init().catch(e => console.error('[PWA] Ошибка инициализации:', e));
        } else {
            // Ждём авторизации
            setTimeout(checkAuthAndInit, 500);
        }
    };

    // Начинаем проверку через 1 секунду после загрузки
    setTimeout(checkAuthAndInit, 1000);
});
