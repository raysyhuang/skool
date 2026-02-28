/* ================================================================
   Skool -- Shared API Helpers
   Vanilla JS fetch wrappers for the game API.
   No frameworks, no dependencies.
   ================================================================ */

(function (root) {
    'use strict';

    /* ──────────────────────────────────────────────
       CSRF Token Helper
       ────────────────────────────────────────────── */

    /**
     * Try to read a CSRF token from the page.
     * Checks, in order:
     *   1. <meta name="csrf-token">
     *   2. <input name="csrf_token"> (hidden form field)
     *   3. Cookie named "csrftoken" or "csrf_token"
     * Returns the token string or null.
     */
    function getCSRFToken() {
        /* 1. <meta> tag */
        var meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');

        /* 2. Hidden input */
        var input = document.querySelector('input[name="csrf_token"]');
        if (input) return input.value;

        /* 3. Cookie */
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var c = cookies[i].trim();
            if (c.indexOf('csrftoken=') === 0) return c.substring(10);
            if (c.indexOf('csrf_token=') === 0) return c.substring(11);
        }

        return null;
    }


    /* ──────────────────────────────────────────────
       Error Toast
       ────────────────────────────────────────────── */

    /**
     * Show a red toast bar at top of screen. Auto-dismisses after 4s.
     * Tap to dismiss early.
     */
    function showError(message) {
        /* Remove existing toast if any */
        var existing = document.getElementById('skool-error-toast');
        if (existing) existing.remove();

        var toast = document.createElement('div');
        toast.id = 'skool-error-toast';
        toast.textContent = message || 'Something went wrong';
        toast.style.cssText =
            'position:fixed;top:0;left:0;right:0;z-index:9999;' +
            'min-height:60px;padding:16px 20px;' +
            'background:#d63031;color:#fff;' +
            'font-size:16px;font-weight:700;' +
            'display:flex;align-items:center;justify-content:center;' +
            'text-align:center;cursor:pointer;' +
            'animation:skoolToastIn 0.3s ease-out;' +
            'font-family:-apple-system,sans-serif;';
        toast.addEventListener('click', function () { toast.remove(); });
        toast.addEventListener('touchend', function (e) { e.preventDefault(); toast.remove(); });
        document.body.appendChild(toast);

        /* Inject keyframes if not already present */
        if (!document.getElementById('skool-toast-style')) {
            var style = document.createElement('style');
            style.id = 'skool-toast-style';
            style.textContent =
                '@keyframes skoolToastIn{from{transform:translateY(-100%)}to{transform:translateY(0)}}' +
                '@keyframes skoolToastOut{from{transform:translateY(0)}to{transform:translateY(-100%)}}';
            document.head.appendChild(style);
        }

        setTimeout(function () {
            if (toast.parentNode) {
                toast.style.animation = 'skoolToastOut 0.3s ease-in forwards';
                setTimeout(function () { if (toast.parentNode) toast.remove(); }, 300);
            }
        }, 4000);
    }


    /* ──────────────────────────────────────────────
       IndexedDB Sync Queue (for offline POST requests)
       ────────────────────────────────────────────── */

    function _openSyncDB() {
        return new Promise(function (resolve, reject) {
            var request = indexedDB.open('skool_sync', 1);
            request.onupgradeneeded = function () {
                var db = request.result;
                if (!db.objectStoreNames.contains('sync_queue')) {
                    db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
                }
            };
            request.onsuccess = function () { resolve(request.result); };
            request.onerror = function () { reject(request.error); };
        });
    }

    function _queueForSync(url, method, body) {
        _openSyncDB().then(function (db) {
            var tx = db.transaction('sync_queue', 'readwrite');
            tx.objectStore('sync_queue').add({
                url: url,
                method: method,
                body: body,
                timestamp: Date.now()
            });
            tx.oncomplete = function () { db.close(); };
        }).catch(function () { /* IndexedDB not available */ });

        /* Register background sync */
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            navigator.serviceWorker.ready.then(function (reg) {
                reg.sync.register('sync-answers');
            }).catch(function () { /* sync not supported */ });
        }
    }


    /* ──────────────────────────────────────────────
       Fetch Wrapper
       ────────────────────────────────────────────── */

    /**
     * Thin wrapper around fetch that:
     *   - Sets Content-Type to application/json
     *   - Attaches CSRF token if available
     *   - Parses JSON response
     *   - Provides consistent error objects
     *
     * @param {string}  url
     * @param {Object}  options          Standard fetch options
     * @param {Object}  [options.body]   Will be JSON.stringified automatically
     * @returns {Promise<Object>}        Parsed JSON body
     */
    function apiFetch(url, options) {
        options = options || {};

        var headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        /* Attach CSRF token */
        var csrf = getCSRFToken();
        if (csrf) {
            headers['X-CSRF-Token'] = csrf;
        }

        /* Merge caller headers */
        if (options.headers) {
            var custom = options.headers;
            for (var key in custom) {
                if (custom.hasOwnProperty(key)) {
                    headers[key] = custom[key];
                }
            }
        }

        var fetchOpts = {
            method: options.method || 'GET',
            headers: headers,
            credentials: 'same-origin'     /* send session cookies */
        };

        if (options.body !== undefined && options.body !== null) {
            fetchOpts.body = typeof options.body === 'string'
                ? options.body
                : JSON.stringify(options.body);
        }

        return fetch(url, fetchOpts)
            .then(function (response) {
                /* Try to parse JSON regardless of status */
                return response.json().then(function (data) {
                    if (!response.ok) {
                        var err = new Error(data.error || data.detail || ('HTTP ' + response.status));
                        err.status = response.status;
                        err.data = data;
                        throw err;
                    }
                    return data;
                });
            })
            .catch(function (err) {
                /* Network errors, JSON parse failures, etc. */
                if (!err.status) {
                    console.error('[Skool API]', err);
                    /* Queue POST requests for background sync when offline */
                    var method = (options.method || 'GET').toUpperCase();
                    if (method === 'POST' && options.body) {
                        var bodyStr = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
                        _queueForSync(url, method, bodyStr);
                        showError('Saved offline. Will sync when connected.');
                    } else {
                        showError('Network error. Check your connection.');
                    }
                }
                throw err;
            });
    }


    /* ──────────────────────────────────────────────
       Public API Helpers
       ────────────────────────────────────────────── */

    /**
     * Submit an answer for a question.
     *
     * POST /game/answer
     * Body: { question_id: int, selected_answer: string }
     *
     * @param {number} questionId
     * @param {string} selectedAnswer
     * @returns {Promise<Object>}  { is_correct, correct_answer, points_earned, question_number }
     */
    function postAnswer(questionId, selectedAnswer) {
        return apiFetch('/game/answer', {
            method: 'POST',
            body: {
                question_id: questionId,
                selected_answer: selectedAnswer
            }
        });
    }

    /**
     * Mark a game session as complete and get the summary.
     *
     * POST /game/complete/{sessionId}
     *
     * @param {number} sessionId
     * @returns {Promise<Object>}  SessionSummary
     */
    function completeSession(sessionId) {
        return apiFetch('/game/complete/' + sessionId, {
            method: 'POST'
        });
    }


    /* ──────────────────────────────────────────────
       Expose on window
       ────────────────────────────────────────────── */

    /**
     * Buy a streak freeze.
     * POST /game/buy-streak-freeze
     */
    function buyStreakFreeze() {
        return apiFetch('/game/buy-streak-freeze', { method: 'POST' });
    }

    /**
     * Buy a store item.
     * POST /game/store/buy
     */
    function buyStoreItem(itemKey) {
        return apiFetch('/game/store/buy', {
            method: 'POST',
            body: { item_key: itemKey }
        });
    }

    /**
     * Equip a store item.
     * POST /game/store/equip
     */
    function equipItem(itemKey) {
        return apiFetch('/game/store/equip', {
            method: 'POST',
            body: { item_key: itemKey }
        });
    }

    root.SkoolAPI = {
        getCSRFToken: getCSRFToken,
        apiFetch: apiFetch,
        postAnswer: postAnswer,
        completeSession: completeSession,
        buyStreakFreeze: buyStreakFreeze,
        buyStoreItem: buyStoreItem,
        equipItem: equipItem,
        showError: showError,
    };

})(window);
