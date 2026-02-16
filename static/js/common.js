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

    root.SkoolAPI = {
        getCSRFToken: getCSRFToken,
        apiFetch: apiFetch,
        postAnswer: postAnswer,
        completeSession: completeSession
    };

})(window);
