/* ================================================================
   Skool -- Text-to-Speech Wrapper
   Uses Google Translate TTS for natural-sounding Chinese pronunciation.
   Falls back to Web Speech API if Google TTS is unavailable.
   ================================================================ */

(function (root) {
    'use strict';

    /* ── Configuration ── */
    var TTS_LANG = 'zh-CN';

    /* ── Google Translate TTS (natural sounding) ── */
    var _ttsAudio = null;

    function speakViaGoogle(text, opts) {
        opts = opts || {};

        /* Use our server-side proxy to Google Translate TTS */
        var url = '/game/tts?text=' + encodeURIComponent(text);

        /* Stop any previous playback */
        if (_ttsAudio) {
            _ttsAudio.pause();
            _ttsAudio.removeAttribute('src');
        }

        _ttsAudio = new Audio(url);
        _ttsAudio.volume = 1.0;

        if (typeof opts.onEnd === 'function') {
            _ttsAudio.onended = opts.onEnd;
        }

        _ttsAudio.onerror = function () {
            /* Google TTS failed — fall back to Web Speech API */
            console.warn('[Skool TTS] Google TTS failed, falling back to Web Speech API.');
            speakViaWebSpeech(text, opts);
        };

        var p = _ttsAudio.play();
        if (p && p.catch) {
            p.catch(function () {
                /* Autoplay blocked — try Web Speech API as fallback */
                speakViaWebSpeech(text, opts);
            });
        }
    }

    /* ── Web Speech API fallback ── */
    var _supported = ('speechSynthesis' in root) && ('SpeechSynthesisUtterance' in root);
    var _cachedVoice = null;

    function findChineseVoice() {
        if (_cachedVoice) return _cachedVoice;
        if (!_supported) return null;

        var voices = root.speechSynthesis.getVoices();
        if (!voices || voices.length === 0) return null;

        var bestMatch = null;
        var fallback = null;

        for (var i = 0; i < voices.length; i++) {
            var v = voices[i];
            var lang = (v.lang || '').replace('_', '-').toLowerCase();

            if (lang === 'zh-cn') {
                bestMatch = v;
                break;
            }
            if (lang.indexOf('zh-cn') === 0 || lang.indexOf('zh-hans') === 0) {
                bestMatch = bestMatch || v;
            }
            if (!fallback && lang.indexOf('zh') === 0) {
                fallback = v;
            }
        }

        _cachedVoice = bestMatch || fallback;
        return _cachedVoice;
    }

    function speakViaWebSpeech(text, opts) {
        opts = opts || {};
        if (!_supported) {
            if (typeof opts.onEnd === 'function') setTimeout(opts.onEnd, 100);
            return;
        }

        var synth = root.speechSynthesis;
        synth.cancel();

        setTimeout(function () {
            var utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = TTS_LANG;
            utterance.rate = 0.75;
            utterance.pitch = 1.15;
            utterance.volume = 1.0;

            var voice = findChineseVoice();
            if (voice) utterance.voice = voice;

            var keepAlive = setInterval(function () {
                if (!synth.speaking) { clearInterval(keepAlive); return; }
                synth.resume();
            }, 3000);

            utterance.onend = function () {
                clearInterval(keepAlive);
                if (typeof opts.onEnd === 'function') opts.onEnd();
            };
            utterance.onerror = function () {
                clearInterval(keepAlive);
            };

            synth.resume();
            synth.speak(utterance);
        }, 50);
    }

    /* ── Init voices for fallback ── */
    if (_supported && root.speechSynthesis.onvoiceschanged !== undefined) {
        root.speechSynthesis.addEventListener('voiceschanged', function () {
            _cachedVoice = null;
            findChineseVoice();
        });
    }

    /* ── Main API: speakChinese ── */
    function speakChinese(text, opts) {
        if (!text) return;
        speakViaGoogle(text, opts);
    }

    /* ── Auto-speak helper ── */
    function autoSpeak(text) {
        if (!text) return;
        setTimeout(function () {
            speakChinese(text);
        }, 500);
    }

    /* ── Expose on window ── */
    root.SkoolTTS = {
        speakChinese: speakChinese,
        autoSpeak: autoSpeak,
        isSupported: function () { return true; }
    };

})(window);
