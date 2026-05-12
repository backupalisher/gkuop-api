/**
 * Модуль аутентификации и управления правами доступа на фронтенде.
 * 
 * Предоставляет:
 * - Аутентификацию через новый механизм (users/permissions)
 * - Функции для проверки прав текущего пользователя
 * - Утилиты для скрытия/блокировки элементов UI на основе прав
 * - CRUD операции с пользователями (для администраторов)
 * - Управление разрешениями пользователей
 */

// ─── Глобальное состояние ───────────────────────────────────────

const AUTH = {
    KEY: 'gkuop_auth_v2',
    _user: null,
    _token: null,
    _permissions: new Set(),
    _initialized: false,

    /** Инициализация модуля */
    init() {
        if (this._initialized) return;
        this._initialized = true;
        this._loadFromStorage();
    },

    /** Сохранение данных в sessionStorage */
    _saveToStorage() {
        try {
            const data = {
                user: this._user,
                token: this._token,
                permissions: Array.from(this._permissions),
                timestamp: Date.now(),
            };
            sessionStorage.setItem(this.KEY, JSON.stringify(data));
        } catch (e) {
            console.warn('Auth: Не удалось сохранить сессию', e);
        }
    },

    /** Загрузка данных из sessionStorage */
    _loadFromStorage() {
        try {
            const raw = sessionStorage.getItem(this.KEY);
            if (!raw) return;

            const data = JSON.parse(raw);
            // Сессия живёт 24 часа
            if (Date.now() - data.timestamp > 24 * 60 * 60 * 1000) {
                sessionStorage.removeItem(this.KEY);
                return;
            }

            this._user = data.user;
            this._token = data.token || null;
            this._permissions = new Set(data.permissions || []);
        } catch (e) {
            console.warn('Auth: Ошибка загрузки сессии', e);
        }
    },

    /** Получение токена для заголовка Authorization */
    getToken() {
        return this._token;
    },

    /** Создание заголовков с авторизацией для fetch-запросов */
    authHeaders(extra = {}) {
        const headers = { ...extra };
        if (this._token) {
            headers['Authorization'] = `Bearer ${this._token}`;
        }
        return headers;
    },

    /** Проверка, аутентифицирован ли пользователь */
    isAuthenticated() {
        return this._user !== null;
    },

    /** Получение текущего пользователя */
    getUser() {
        return this._user;
    },

    /** Получение роли текущего пользователя */
    getRole() {
        return this._user ? this._user.role : null;
    },

    /** Проверка, является ли пользователь администратором */
    isAdmin() {
        return this._user && this._user.role === 'admin';
    },

    /** Получение списка разрешений */
    getPermissions() {
        return Array.from(this._permissions);
    },

    /**
     * Проверка наличия конкретного разрешения.
     * Администратор имеет все права.
     */
    hasPermission(permissionCode) {
        if (this.isAdmin()) return true;
        return this._permissions.has(permissionCode);
    },

    /**
     * Проверка наличия нескольких разрешений (И).
     * Возвращает true, если есть ВСЕ указанные разрешения.
     */
    hasAllPermissions(...permissionCodes) {
        if (this.isAdmin()) return true;
        return permissionCodes.every(code => this._permissions.has(code));
    },

    /**
     * Проверка наличия хотя бы одного из указанных разрешений (ИЛИ).
     */
    hasAnyPermission(...permissionCodes) {
        if (this.isAdmin()) return true;
        return permissionCodes.some(code => this._permissions.has(code));
    },

    /**
     * Аутентификация пользователя.
     * @param {string} username
     * @param {string} password
     * @returns {Promise<object>} Результат аутентификации
     */
    async login(username, password) {
        const response = await fetch('/api/auth/login-new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (data.status === 'ok') {
            this._user = data.user;
            this._token = data.token || null;
            this._permissions = new Set(data.permissions || []);
            this._saveToStorage();
            return { success: true, user: data.user, token: data.token, permissions: data.permissions };
        }

        return { success: false, error: data.message || 'Ошибка аутентификации' };
    },

    /** Выход из системы */
    logout() {
        this._user = null;
        this._token = null;
        this._permissions = new Set();
        sessionStorage.removeItem(this.KEY);
        // Останавливаем PermissionGuard при выходе
        if (typeof PermissionGuard !== 'undefined') {
            PermissionGuard._stopObserver();
        }
    },

    /**
     * Проверка разрешений на сервере (для критических операций).
     * @param {string[]} permissions - массив кодов разрешений
     * @returns {Promise<object>} Результаты проверки
     */
    async checkPermissionsOnServer(permissions) {
        try {
            const response = await fetch('/api/auth/check-permissions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ permissions }),
            });
            const data = await response.json();
            return data.results || {};
        } catch (e) {
            console.error('Auth: Ошибка проверки прав на сервере', e);
            return {};
        }
    },

    /** Обновление информации о пользователе с сервера */
    async refresh() {
        try {
            const headers = {};
            if (this._token) {
                headers['Authorization'] = `Bearer ${this._token}`;
            }
            const response = await fetch('/api/auth/me', { headers });
            if (!response.ok) {
                this.logout();
                return false;
            }
            const data = await response.json();
            this._user = data.user;
            this._permissions = new Set(data.permissions || []);
            this._saveToStorage();
            return true;
        } catch (e) {
            console.error('Auth: Ошибка обновления', e);
            return false;
        }
    }
};


// ─── Управление UI на основе прав ───────────────────────────────

const PermissionUI = {
    /**
     * Скрыть элементы, для которых у пользователя нет прав.
     * Элементы должны иметь атрибут data-permission.
     * 
     * Пример: <button data-permission="edit_tickets">Редактировать</button>
     * 
     * Если нужно несколько разрешений (И): data-permission="perm1,perm2"
     * Если нужно хотя бы одно (ИЛИ): data-permission-any="perm1,perm2"
     */
    apply() {
        // Скрываем элементы, требующие конкретных разрешений (И)
        document.querySelectorAll('[data-permission]').forEach(el => {
            const required = el.getAttribute('data-permission').split(',').map(s => s.trim());
            const hasAccess = AUTH.hasAllPermissions(...required);
            el.style.display = hasAccess ? '' : 'none';
        });

        // Скрываем элементы, требующие хотя бы одного разрешения (ИЛИ)
        document.querySelectorAll('[data-permission-any]').forEach(el => {
            const required = el.getAttribute('data-permission-any').split(',').map(s => s.trim());
            const hasAccess = AUTH.hasAnyPermission(...required);
            el.style.display = hasAccess ? '' : 'none';
        });

        // Блокируем (disable) элементы с data-permission-disable
        document.querySelectorAll('[data-permission-disable]').forEach(el => {
            const required = el.getAttribute('data-permission-disable').split(',').map(s => s.trim());
            const hasAccess = AUTH.hasAllPermissions(...required);
            if (!hasAccess) {
                el.disabled = true;
                el.title = el.title || 'Недостаточно прав для выполнения этого действия';
                el.classList.add('disabled-by-permission');
            }
        });

        // Показываем элементы для администраторов
        document.querySelectorAll('[data-role="admin"]').forEach(el => {
            el.style.display = AUTH.isAdmin() ? '' : 'none';
        });

        // Показываем элементы для операторов
        document.querySelectorAll('[data-role="operator"]').forEach(el => {
            el.style.display = AUTH.getRole() === 'operator' ? '' : 'none';
        });
    },

    /**
     * Обновить UI после изменения прав (перерисовка).
     * Вызывать после загрузки нового контента через AJAX.
     */
    refresh() {
        this.apply();
    },

    /**
     * Создать HTML-элемент с проверкой прав.
     * @param {string} tag - HTML-тег
     * @param {object} attrs - атрибуты элемента
     * @param {string|string[]} permission - требуемое разрешение
     * @param {boolean} anyMode - если true, используется data-permission-any
     * @returns {HTMLElement|null} - элемент или null, если нет прав
     */
    createElement(tag, attrs = {}, permission = null, anyMode = false) {
        if (permission) {
            const perms = Array.isArray(permission) ? permission : [permission];
            const hasAccess = anyMode
                ? AUTH.hasAnyPermission(...perms)
                : AUTH.hasAllPermissions(...perms);

            if (!hasAccess) return null;
        }

        const el = document.createElement(tag);
        Object.entries(attrs).forEach(([key, value]) => {
            if (key === 'className') {
                el.className = value;
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(el.style, value);
            } else if (key.startsWith('data-')) {
                el.setAttribute(key, value);
            } else if (key === 'innerHTML') {
                el.innerHTML = value;
            } else if (key === 'textContent') {
                el.textContent = value;
            } else {
                el[key] = value;
            }
        });

        return el;
    }
};


// ─── PermissionGuard: централизованная защита UI ─────────────────

/**
 * PermissionGuard — централизованный механизм динамического скрытия
 * элементов интерфейса на основе прав доступа пользователя.
 *
 * Возможности:
 * - Автоматическое скрытие элементов с data-permission при загрузке
 * - MutationObserver для динамически добавляемых элементов
 * - Защита функций-обработчиков (даже при вызове из консоли)
 * - Единая точка проверки для всех представлений
 * - Обновление интерфейса при изменении прав в реальном времени
 *
 * Использование в HTML:
 *   <button data-permission="edit_tickets">Редактировать</button>
 *   <button data-permission="archive_tickets,delete_tickets">Опасно</button>
 *   <button data-permission-any="view_logs,export_data">Логи/Экспорт</button>
 *   <div data-permission-disable="edit_tickets">...</div>
 *   <div data-role="admin">Только для админов</div>
 *
 * Использование в JS:
 *   PermissionGuard.protectFunction(fn, 'edit_tickets') — обёртка с проверкой
 *   PermissionGuard.createElement('button', {...}, 'edit_tickets') — создание
 *   PermissionGuard.guardElement(el, 'edit_tickets') — защита существующего
 *   PermissionGuard.refresh() — переприменить ко всему DOM
 */
const PermissionGuard = {
    /** Флаг активности MutationObserver */
    _observerActive: false,
    /** Ссылка на MutationObserver */
    _observer: null,

    /**
     * Инициализация: применяет защиту ко всему DOM и запускает MutationObserver.
     * Вызывается один раз после загрузки auth.js.
     */
    init() {
        this.apply();
        this._startObserver();
    },

    /**
     * Применить защиту ко всем элементам в DOM.
     * Безопасно вызывать многократно — повторно не обрабатывает уже защищённые.
     */
    apply() {
        // 1. Скрываем элементы, требующие конкретных разрешений (И)
        document.querySelectorAll('[data-permission]:not([data-guard-processed])').forEach(el => {
            this.guardElement(el);
        });

        // 2. Скрываем элементы, требующие хотя бы одного разрешения (ИЛИ)
        document.querySelectorAll('[data-permission-any]:not([data-guard-processed])').forEach(el => {
            this.guardElementAny(el);
        });

        // 3. Блокируем (disable) элементы с data-permission-disable
        document.querySelectorAll('[data-permission-disable]:not([data-guard-processed])').forEach(el => {
            this.guardElementDisable(el);
        });

        // 4. Обрабатываем data-role
        document.querySelectorAll('[data-role]:not([data-guard-processed])').forEach(el => {
            this.guardElementByRole(el);
        });
    },

    /**
     * Защитить один элемент с data-permission (все разрешения обязательны).
     * @param {HTMLElement} el
     */
    guardElement(el) {
        const required = el.getAttribute('data-permission').split(',').map(s => s.trim());
        const hasAccess = AUTH.hasAllPermissions(...required);
        if (!hasAccess) {
            el.style.display = 'none';
            el.setAttribute('aria-hidden', 'true');
        }
        el.setAttribute('data-guard-processed', 'true');
    },

    /**
     * Защитить элемент с data-permission-any (хотя бы одно разрешение).
     * @param {HTMLElement} el
     */
    guardElementAny(el) {
        const required = el.getAttribute('data-permission-any').split(',').map(s => s.trim());
        const hasAccess = AUTH.hasAnyPermission(...required);
        if (!hasAccess) {
            el.style.display = 'none';
            el.setAttribute('aria-hidden', 'true');
        }
        el.setAttribute('data-guard-processed', 'true');
    },

    /**
     * Заблокировать (disabled) элемент с data-permission-disable.
     * @param {HTMLElement} el
     */
    guardElementDisable(el) {
        const required = el.getAttribute('data-permission-disable').split(',').map(s => s.trim());
        const hasAccess = AUTH.hasAllPermissions(...required);
        if (!hasAccess) {
            el.disabled = true;
            el.title = el.title || 'Недостаточно прав для выполнения этого действия';
            el.classList.add('disabled-by-permission');
        }
        el.setAttribute('data-guard-processed', 'true');
    },

    /**
     * Защитить элемент с data-role (admin/operator).
     * @param {HTMLElement} el
     */
    guardElementByRole(el) {
        const role = el.getAttribute('data-role');
        if (role === 'admin') {
            el.style.display = AUTH.isAdmin() ? '' : 'none';
        } else if (role === 'operator') {
            el.style.display = AUTH.getRole() === 'operator' ? '' : 'none';
        }
        el.setAttribute('data-guard-processed', 'true');
    },

    /**
     * Создать элемент с проверкой прав.
     * @param {string} tag - HTML-тег
     * @param {object} attrs - атрибуты
     * @param {string|string[]} [permission] - требуемое разрешение
     * @param {boolean} [anyMode=false] - ИЛИ вместо И
     * @returns {HTMLElement|null} элемент или null если нет прав
     */
    createElement(tag, attrs = {}, permission = null, anyMode = false) {
        if (permission) {
            const perms = Array.isArray(permission) ? permission : [permission];
            const hasAccess = anyMode
                ? AUTH.hasAnyPermission(...perms)
                : AUTH.hasAllPermissions(...perms);
            if (!hasAccess) return null;
        }
        const el = document.createElement(tag);
        Object.entries(attrs).forEach(([key, value]) => {
            if (key === 'className') el.className = value;
            else if (key === 'style' && typeof value === 'object') Object.assign(el.style, value);
            else if (key.startsWith('data-')) el.setAttribute(key, value);
            else if (key === 'innerHTML') el.innerHTML = value;
            else if (key === 'textContent') el.textContent = value;
            else el[key] = value;
        });
        return el;
    },

    /**
     * Обернуть функцию проверкой прав.
     * Если у пользователя нет указанного разрешения, функция не выполняется
     * и показывается toast с предупреждением.
     *
     * @param {Function} fn - исходная функция
     * @param {string|string[]} permission - требуемое разрешение (разрешения)
     * @param {boolean} [anyMode=false] - ИЛИ вместо И
     * @param {string} [errorMessage] - сообщение при отсутствии прав
     * @returns {Function} обёрнутая функция
     *
     * @example
     *   const safeDelete = PermissionGuard.protectFunction(deleteImage, 'delete_images');
     *   // Теперь safeDelete() проверит права перед вызовом
     */
    protectFunction(fn, permission, anyMode = false, errorMessage = null) {
        const perms = Array.isArray(permission) ? permission : [permission];
        return function(...args) {
            const hasAccess = anyMode
                ? AUTH.hasAnyPermission(...perms)
                : AUTH.hasAllPermissions(...perms);

            if (!hasAccess) {
                const msg = errorMessage || `Недостаточно прав для выполнения операции`;
                console.warn(`[PermissionGuard] ⛔ Доступ запрещён: ${msg}`);
                // Пытаемся показать toast, если функция доступна
                if (typeof showToast === 'function') {
                    showToast(msg, 'error');
                }
                return false;
            }
            return fn.apply(this, args);
        };
    },

    /**
     * Запустить MutationObserver для автоматической защиты новых DOM-элементов.
     */
    _startObserver() {
        if (this._observerActive) return;
        this._observerActive = true;

        this._observer = new MutationObserver((mutations) => {
            let needsApply = false;
            for (const mutation of mutations) {
                if (mutation.addedNodes.length > 0) {
                    needsApply = true;
                    break;
                }
            }
            if (needsApply) {
                // Небольшая задержка, чтобы DOM успел обновиться
                clearTimeout(this._observerTimeout);
                this._observerTimeout = setTimeout(() => this.apply(), 50);
            }
        });

        this._observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    },

    /**
     * Остановить MutationObserver (например, при разлогине).
     */
    _stopObserver() {
        if (this._observer) {
            this._observer.disconnect();
            this._observer = null;
        }
        this._observerActive = false;
    },

    /**
     * Полное обновление: сбросить флаги processed и переприменить.
     * Вызывать после изменения прав пользователя.
     */
    refresh() {
        // Сбрасываем флаги processed
        document.querySelectorAll('[data-guard-processed]').forEach(el => {
            el.removeAttribute('data-guard-processed');
            // Восстанавливаем display если был скрыт
            if (el.style.display === 'none' && !el.hasAttribute('data-force-hidden')) {
                el.style.display = '';
            }
            el.removeAttribute('aria-hidden');
            if (el.disabled) {
                el.disabled = false;
                el.classList.remove('disabled-by-permission');
            }
        });
        this.apply();
    },

    /**
     * Обновление прав пользователя с сервера и переприменение UI.
     * @returns {Promise<boolean>}
     */
    async refreshFromServer() {
        const success = await AUTH.refresh();
        if (success) {
            this.refresh();
        }
        return success;
    }
};


// ─── CRUD операции с пользователями ────────────────────────────

const UserManager = {
    /**
     * Выполнить fetch-запрос с авторизацией.
     * @param {string} url
     * @param {object} options
     * @returns {Promise<Response>}
     */
    async _fetch(url, options = {}) {
        const headers = AUTH.authHeaders(options.headers || {});
        const response = await fetch(url, { ...options, headers });
        return response;
    },

    /**
     * Получение списка всех пользователей.
     * @returns {Promise<Array>}
     */
    async getUsers() {
        const response = await this._fetch('/api/auth/users');
        if (!response.ok) throw new Error('Ошибка загрузки пользователей');
        const data = await response.json();
        return data.users || [];
    },

    /**
     * Получение информации о пользователе.
     * @param {string} username
     * @returns {Promise<object>}
     */
    async getUser(username) {
        const response = await this._fetch(`/api/auth/users/${encodeURIComponent(username)}`);
        if (!response.ok) throw new Error('Пользователь не найден');
        return response.json();
    },

    /**
     * Создание нового пользователя.
     * @param {object} userData - { username, password, role, full_name, email }
     * @returns {Promise<object>}
     */
    async createUser(userData) {
        const response = await this._fetch('/api/auth/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Ошибка создания пользователя');
        return data;
    },

    /**
     * Обновление данных пользователя.
     * @param {string} username
     * @param {object} updates - { full_name?, email?, role?, is_active?, password? }
     * @returns {Promise<object>}
     */
    async updateUser(username, updates) {
        const response = await this._fetch(`/api/auth/users/${encodeURIComponent(username)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Ошибка обновления пользователя');
        return data;
    },

    /**
     * Удаление пользователя.
     * @param {string} username
     * @returns {Promise<object>}
     */
    async deleteUser(username) {
        const response = await this._fetch(`/api/auth/users/${encodeURIComponent(username)}`, {
            method: 'DELETE',
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Ошибка удаления пользователя');
        return data;
    },

    /**
     * Получение разрешений пользователя.
     * @param {string} username
     * @returns {Promise<object>} - { user, permissions, catalog }
     */
    async getUserPermissions(username) {
        const response = await this._fetch(`/api/auth/users/${encodeURIComponent(username)}/permissions`);
        if (!response.ok) throw new Error('Ошибка загрузки разрешений');
        return response.json();
    },

    /**
     * Массовое обновление разрешений пользователя.
     * @param {string} username
     * @param {object} permissions - { permission_code: true/false, ... }
     * @returns {Promise<object>}
     */
    async updatePermissions(username, permissions) {
        const response = await this._fetch(`/api/auth/users/${encodeURIComponent(username)}/permissions`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ permissions }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Ошибка обновления разрешений');
        return data;
    },

    /**
     * Сброс разрешений пользователя до базовых по его роли.
     * @param {string} username
     * @returns {Promise<object>}
     */
    async resetPermissions(username) {
        const response = await this._fetch(`/api/auth/users/${encodeURIComponent(username)}/permissions/reset`, {
            method: 'POST',
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Ошибка сброса разрешений');
        return data;
    },

    /**
     * Получение каталога всех разрешений.
     * @returns {Promise<Array>}
     */
    async getPermissionsCatalog() {
        const response = await this._fetch('/api/auth/permissions/catalog');
        if (!response.ok) throw new Error('Ошибка загрузки каталога разрешений');
        const data = await response.json();
        return data.permissions || [];
    }
};


// ─── Компоненты UI для управления пользователями ───────────────

const UserUI = {
    /**
     * Экранирование HTML-спецсимволов для безопасной вставки в innerHTML.
     * @param {string} text
     * @returns {string}
     */
    escapeHtml(text) {
        if (text == null) return '';
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(String(text)));
        return div.innerHTML;
    },

    /**
     * Создать модальное окно для добавления/редактирования пользователя.
     * @param {object} options - { user (для редактирования), onSave }
     * @returns {HTMLElement}
     */
    createUserFormModal(options = {}) {
        const { user = null, onSave } = options;
        const isEdit = user !== null;

        const modal = createModalOverlay();
        modal.innerHTML = `
            <div class="modal-content modal-user-form">
                <h3>${isEdit ? 'Редактирование пользователя' : 'Добавление пользователя'}</h3>
                <form id="userForm">
                    <div class="form-group">
                        <label>Логин</label>
                        <input type="text" name="username" class="input" 
                               value="${UserUI.escapeHtml(isEdit ? user.username : '')}" 
                               ${isEdit ? 'readonly' : 'required'}>
                    </div>
                    <div class="form-group">
                        <label>Пароль ${isEdit ? '(оставьте пустым, чтобы не менять)' : ''}</label>
                        <input type="password" name="password" class="input" 
                               ${isEdit ? '' : 'required'}>
                    </div>
                    <div class="form-group">
                        <label>Полное имя</label>
                        <input type="text" name="full_name" class="input" 
                               value="${UserUI.escapeHtml((user && user.full_name) || '')}">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" class="input" 
                               value="${UserUI.escapeHtml((user && user.email) || '')}">
                    </div>
                    <div class="form-group">
                        <label>Роль</label>
                        <select name="role" class="input">
                            <option value="operator" ${user && user.role === 'operator' ? 'selected' : ''}>
                                Оператор
                            </option>
                            <option value="admin" ${user && user.role === 'admin' ? 'selected' : ''}>
                                Администратор
                            </option>
                        </select>
                    </div>
                    ${isEdit ? `
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="is_active" value="1" 
                                   ${user.is_active !== false ? 'checked' : ''}>
                            Активен
                        </label>
                    </div>` : ''}
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">
                            ${isEdit ? 'Сохранить' : 'Создать'}
                        </button>
                        <button type="button" class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">
                            Отмена
                        </button>
                    </div>
                </form>
                <div class="form-error" style="color:red;margin-top:8px;display:none"></div>
            </div>
        `;

        modal.querySelector('#userForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const errorEl = modal.querySelector('.form-error');
            errorEl.style.display = 'none';

            const formData = new FormData(form);
            const data = {
                username: formData.get('username').trim(),
                password: formData.get('password').trim(),
                role: formData.get('role'),
                full_name: formData.get('full_name').trim() || undefined,
                email: formData.get('email').trim() || undefined,
            };

            if (isEdit) {
                // Для редактирования отправляем только изменяемые поля
                const updates = {};
                if (data.password) updates.password = data.password;
                if (data.full_name !== undefined) updates.full_name = data.full_name;
                if (data.email !== undefined) updates.email = data.email;
                if (data.role) updates.role = data.role;
                updates.is_active = formData.get('is_active') === '1';

                try {
                    const result = await UserManager.updateUser(user.username, updates);
                    if (onSave) onSave(result);
                    modal.remove();
                } catch (err) {
                    errorEl.textContent = err.message;
                    errorEl.style.display = 'block';
                }
            } else {
                try {
                    const result = await UserManager.createUser(data);
                    if (onSave) onSave(result);
                    modal.remove();
                } catch (err) {
                    errorEl.textContent = err.message;
                    errorEl.style.display = 'block';
                }
            }
        });

        return modal;
    },

    /**
     * Создать модальное окно управления разрешениями пользователя.
     * @param {string} username
     * @returns {Promise<HTMLElement>}
     */
    async createPermissionsModal(username) {
        const data = await UserManager.getUserPermissions(username);
        const catalog = data.catalog || [];
        const permissions = data.permissions || [];
        const permMap = {};
        permissions.forEach(p => { permMap[p.permission_code] = p.granted; });

        // Группируем разрешения по категориям
        const categories = {};
        catalog.forEach(p => {
            const cat = p.category || 'other';
            if (!categories[cat]) categories[cat] = [];
            categories[cat].push(p);
        });

        const categoryLabels = {
            'tickets': 'Заявки',
            'tasks': 'Задачи',
            'images': 'Изображения',
            'users': 'Пользователи',
            'system': 'Системные',
            'other': 'Прочее',
        };

        const modal = createModalOverlay();
        modal.innerHTML = `
            <div class="modal-content modal-permissions" style="max-width:700px">
                <h3>Управление правами: ${UserUI.escapeHtml(username)}</h3>
                <div class="permissions-container">
                    ${Object.entries(categories).map(([cat, perms]) => `
                        <div class="permission-category">
                            <h4>${categoryLabels[cat] || cat}</h4>
                            ${perms.map(p => {
                                const granted = permMap[p.code] !== false;
                                return `
                                    <label class="permission-item">
                                        <input type="checkbox" class="perm-checkbox" 
                                               data-code="${p.code}" 
                                               ${granted ? 'checked' : ''}>
                                        <span class="perm-name">${p.name}</span>
                                        <span class="perm-desc">${p.description || ''}</span>
                                    </label>
                                `;
                            }).join('')}
                        </div>
                    `).join('')}
                </div>
                <div class="form-actions">
                    <button class="btn btn-primary" id="savePermissionsBtn">Сохранить</button>
                    <button class="btn btn-secondary" id="resetPermissionsBtn">Сбросить до роли</button>
                    <button class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">Отмена</button>
                </div>
                <div class="form-error" style="color:red;margin-top:8px;display:none"></div>
            </div>
        `;

        // Сохранение разрешений
        modal.querySelector('#savePermissionsBtn').addEventListener('click', async () => {
            const checkboxes = modal.querySelectorAll('.perm-checkbox');
            const permissionsData = {};
            checkboxes.forEach(cb => {
                permissionsData[cb.dataset.code] = cb.checked;
            });

            const errorEl = modal.querySelector('.form-error');
            errorEl.style.display = 'none';

            try {
                await UserManager.updatePermissions(username, permissionsData);
                modal.remove();
                // Показываем уведомление
                showToast('Права пользователя обновлены', 'success');
            } catch (err) {
                errorEl.textContent = err.message;
                errorEl.style.display = 'block';
            }
        });

        // Сброс до роли
        modal.querySelector('#resetPermissionsBtn').addEventListener('click', async () => {
            if (!confirm('Сбросить все разрешения до стандартных для этой роли?')) return;

            try {
                const result = await UserManager.resetPermissions(username);
                // Обновляем чекбоксы
                const newPerms = result.permissions || [];
                const newPermMap = {};
                newPerms.forEach(p => { newPermMap[p.permission_code] = p.granted; });

                modal.querySelectorAll('.perm-checkbox').forEach(cb => {
                    cb.checked = newPermMap[cb.dataset.code] !== false;
                });

                showToast('Права сброшены до базовых по роли', 'success');
            } catch (err) {
                const errorEl = modal.querySelector('.form-error');
                errorEl.textContent = err.message;
                errorEl.style.display = 'block';
            }
        });

        return modal;
    },

    /**
     * Создать HTML-таблицу пользователей для панели администратора.
     * @param {Array} users - список пользователей
     * @returns {HTMLElement}
     */
    createUsersTable(users) {
        const table = document.createElement('table');
        table.className = 'users-table';

        // Создаём thead через DOM (безопасно, без пользовательских данных)
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        ['Логин', 'Имя', 'Роль', 'Email', 'Статус', 'Последний вход', 'Действия'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Создаём tbody через DOM (безопасно — textContent экранирует HTML)
        const tbody = document.createElement('tbody');
        users.forEach(u => {
            const tr = document.createElement('tr');

            // Логин
            const tdLogin = document.createElement('td');
            const strong = document.createElement('strong');
            strong.textContent = u.username || '';
            tdLogin.appendChild(strong);
            tr.appendChild(tdLogin);

            // Имя
            const tdName = document.createElement('td');
            tdName.textContent = u.full_name || '—';
            tr.appendChild(tdName);

            // Роль
            const tdRole = document.createElement('td');
            const roleSpan = document.createElement('span');
            roleSpan.className = `role-badge role-${u.role || ''}`;
            roleSpan.textContent = u.role === 'admin' ? 'Админ' : 'Оператор';
            tdRole.appendChild(roleSpan);
            tr.appendChild(tdRole);

            // Email
            const tdEmail = document.createElement('td');
            tdEmail.textContent = u.email || '—';
            tr.appendChild(tdEmail);

            // Статус
            const tdStatus = document.createElement('td');
            tdStatus.textContent = u.is_active !== false ? '✅ Активен' : '❌ Неактивен';
            tr.appendChild(tdStatus);

            // Последний вход
            const tdLastLogin = document.createElement('td');
            tdLastLogin.textContent = u.last_login ? new Date(u.last_login).toLocaleString() : '—';
            tr.appendChild(tdLastLogin);

            // Действия
            const tdActions = document.createElement('td');
            tdActions.className = 'actions-cell';

            const btnPermissions = document.createElement('button');
            btnPermissions.className = 'btn btn-sm';
            btnPermissions.setAttribute('data-permission', 'manage_permissions');
            btnPermissions.textContent = '🔑 Права';
            btnPermissions.onclick = () => UserUI.openPermissionsModal(u.username);
            tdActions.appendChild(btnPermissions);

            const btnEdit = document.createElement('button');
            btnEdit.className = 'btn btn-sm';
            btnEdit.setAttribute('data-permission', 'manage_users');
            btnEdit.textContent = '✏️';
            btnEdit.onclick = () => UserUI.openEditModal(u.username);
            tdActions.appendChild(btnEdit);

            const btnDelete = document.createElement('button');
            btnDelete.className = 'btn btn-sm btn-danger';
            btnDelete.setAttribute('data-permission', 'manage_users');
            btnDelete.textContent = '🗑️';
            btnDelete.onclick = () => UserUI.confirmDelete(u.username);
            tdActions.appendChild(btnDelete);

            tr.appendChild(tdActions);
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        return table;
    },

    /** Открыть модальное окно редактирования пользователя */
    async openEditModal(username) {
        try {
            const data = await UserManager.getUser(username);
            const modal = UserUI.createUserFormModal({
                user: data.user,
                onSave: (result) => {
                    showToast(`Пользователь ${username} обновлён`, 'success');
                    // Обновляем таблицу в модальном окне, если оно открыто
                    const container = document.getElementById('usersTableContainer');
                    if (container && typeof openUsersModal === 'function') {
                        // Перезагружаем данные в текущем модальном окне
                        UserManager.getUsers()
                            .then(users => {
                                const table = UserUI.createUsersTable(users);
                                container.innerHTML = '';
                                container.appendChild(table);
                                if (typeof applyPermissionUI === 'function') {
                                    setTimeout(applyPermissionUI, 50);
                                }
                            })
                            .catch(err => {
                                container.innerHTML = `<p class="error-msg">Ошибка: ${UserUI.escapeHtml(err.message)}</p>`;
                            });
                    }
                }
            });
            document.body.appendChild(modal);
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    /** Открыть модальное окно создания нового пользователя */
    openCreateModal() {
        const modal = UserUI.createUserFormModal({
            user: null,
            onSave: (result) => {
                showToast('Пользователь создан', 'success');
                // Обновляем таблицу в модальном окне, если оно открыто
                const container = document.getElementById('usersTableContainer');
                if (container) {
                    UserManager.getUsers()
                        .then(users => {
                            const table = UserUI.createUsersTable(users);
                            container.innerHTML = '';
                            container.appendChild(table);
                            if (typeof applyPermissionUI === 'function') {
                                setTimeout(applyPermissionUI, 50);
                            }
                        })
                        .catch(err => {
                            container.innerHTML = `<p class="error-msg">Ошибка: ${UserUI.escapeHtml(err.message)}</p>`;
                        });
                }
            }
        });
        document.body.appendChild(modal);
    },

    /** Открыть модальное окно управления правами */
    async openPermissionsModal(username) {
        try {
            const modal = await UserUI.createPermissionsModal(username);
            document.body.appendChild(modal);
        } catch (err) {
            showToast(err.message, 'error');
        }
    },

    /** Подтверждение удаления пользователя */
    async confirmDelete(username) {
        if (!confirm(`Вы уверены, что хотите удалить пользователя "${username}"?`)) return;

        try {
            await UserManager.deleteUser(username);
            showToast(`Пользователь ${username} удалён`, 'success');
            const container = document.getElementById('usersTableContainer');
            if (container) {
                try {
                    const users = await UserManager.getUsers();
                    const table = UserUI.createUsersTable(users);
                    container.innerHTML = '';
                    container.appendChild(table);
                    if (typeof applyPermissionUI === 'function') {
                        setTimeout(applyPermissionUI, 50);
                    }
                } catch (err) {
                    container.innerHTML = `<p class="error-msg">Ошибка: ${UserUI.escapeHtml(err.message)}</p>`;
                }
            }
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
};


// ─── Интеграция с существующей системой аутентификации ─────────

/**
 * Расширенная функция логина, поддерживающая оба механизма:
 * старый (login/password hash) и новый (users/permissions).
 * 
 * Используется как замена существующей handleLogin.
 */
async function handleLoginV2(event) {
    event.preventDefault();

    const login = document.getElementById('authLogin')?.value?.trim();
    const password = document.getElementById('authPassword')?.value?.trim();
    const errorEl = document.getElementById('authError');

    if (!login || !password) {
        if (errorEl) errorEl.textContent = 'Введите логин и пароль';
        return false;
    }

    try {
        // Пробуем новый механизм аутентификации (users/permissions)
        const result = await AUTH.login(login, password);

        if (result.success) {
            // Успешный вход через новый механизм
            if (errorEl) errorEl.textContent = '';
            document.getElementById('authOverlay').style.display = 'none';
            const indicator = document.getElementById('authIndicator');
            if (indicator) {
                indicator.style.display = 'flex';
                const nameEl = indicator.querySelector('.auth-indicator');
                if (nameEl) nameEl.innerHTML = '<span class="auth-dot"></span>' + (result.user?.username || login);
            }
            // Сохраняем также под старым ключом для совместимости с ticket_detail.html
            try {
                sessionStorage.setItem('gkuop_auth', JSON.stringify({
                    username: result.user?.username || login,
                    timestamp: Date.now()
                }));
            } catch (e) { /* ignore */ }
            // Инициализируем PermissionGuard (применяет защиту + MutationObserver)
            PermissionGuard.init();
            // Показываем вкладку пользователей если admin
            if (typeof updateUsersTabVisibility === 'function') {
                updateUsersTabVisibility();
            }
            if (typeof loadTickets === 'function') loadTickets();
            if (typeof loadTicket === 'function') loadTicket();
            return false;
        }

        // Новый механизм не сработал — пробуем старый (для обратной совместимости)
        const oldResponse = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ login, password }),
        });

        const oldData = await oldResponse.json();

        if (oldData.status === 'ok') {
            // Старый механизм сработал — показываем сообщение о необходимости
            // создать учётную запись через seed_admin.py или админ-панель
            if (errorEl) {
                errorEl.textContent = 'Старая система аутентификации отключена. '
                    + 'Обратитесь к администратору для создания учётной записи.';
            }
            return false;
        }

        // Оба механизма не сработали
        if (errorEl) errorEl.textContent = oldData.message || 'Неверный логин или пароль';
        return false;

    } catch (e) {
        console.error('Login error:', e);
        if (errorEl) errorEl.textContent = 'Ошибка соединения с сервером';
        return false;
    }
}


// ─── Вспомогательные функции ────────────────────────────────────

/**
 * Создать модальное окно с автоматическим z-index,
 * чтобы вложенные модальные окна не перекрывались.
 * @param {string} className - класс для overlay
 * @returns {HTMLDivElement} элемент overlay
 */
function createModalOverlay(className = 'modal-overlay') {
    const overlay = document.createElement('div');
    overlay.className = className;
    // Автоматически поднимаем z-index выше всех существующих overlay
    const existingOverlays = document.querySelectorAll('.modal-overlay');
    const baseZ = 950; // --z-modal
    const offset = existingOverlays.length * 10;
    overlay.style.zIndex = String(baseZ + offset);
    return overlay;
}

/**
 * Применить права доступа к UI.
 * Вызывается после аутентификации и после загрузки динамического контента.
 * Использует централизованный PermissionGuard.
 */
function applyPermissionUI() {
    PermissionGuard.apply();
}

/**
 * Показать уведомление (тост).
 * @param {string} message
 * @param {'success'|'error'|'info'|'warning'} type
 * @param {number} [duration=6000] - время показа в мс (0 — не закрывать автоматически)
 */
function showToast(message, type = 'info', duration = 6000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    // Иконки для каждого типа уведомления
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ',
    };
    const icon = icons[type] || icons.info;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');

    // Иконка
    const iconSpan = document.createElement('span');
    iconSpan.className = 'toast-icon';
    iconSpan.textContent = icon;

    // Текст сообщения
    const textSpan = document.createElement('span');
    textSpan.className = 'toast-text';
    textSpan.textContent = message;

    // Кнопка закрытия
    const closeBtn = document.createElement('button');
    closeBtn.className = 'toast-close';
    closeBtn.setAttribute('aria-label', 'Закрыть');
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', () => {
        toast.classList.add('toast-fadeout');
        setTimeout(() => toast.remove(), 300);
    });

    toast.appendChild(iconSpan);
    toast.appendChild(textSpan);
    toast.appendChild(closeBtn);
    container.appendChild(toast);

    // Автоматическое закрытие
    if (duration > 0) {
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.add('toast-fadeout');
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
    }
}


// ─── Экспорт в глобальную область видимости ─────────────────────

window.AUTH = AUTH;
window.PermissionUI = PermissionUI;
window.PermissionGuard = PermissionGuard;
window.UserManager = UserManager;
window.UserUI = UserUI;
window.handleLoginV2 = handleLoginV2;
window.applyPermissionUI = applyPermissionUI;
window.showToast = showToast;
window.createModalOverlay = createModalOverlay;

// Автоинициализация при загрузке страницы
AUTH.init();
