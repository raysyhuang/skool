/* ================================================================
   Skool -- Text-to-Speech Wrapper
   Uses Google Translate TTS for natural-sounding Chinese pronunciation.
   Falls back to Web Speech API if Google TTS is unavailable.
   ================================================================ */

(function (root) {
    'use strict';

    /* ── Configuration ── */
    var DEFAULT_LANG = 'zh-CN';

    /* ── Google Translate TTS (natural sounding) ── */
    var _ttsAudio = null;

    function speakViaGoogle(text, lang, opts) {
        opts = opts || {};
        lang = lang || DEFAULT_LANG;

        /* Use our server-side proxy to Google Translate TTS */
        var url = '/game/tts?text=' + encodeURIComponent(text) + '&lang=' + encodeURIComponent(lang);

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
            speakViaWebSpeech(text, lang, opts);
        };

        var p = _ttsAudio.play();
        if (p && p.catch) {
            p.catch(function () {
                /* Autoplay blocked — try Web Speech API as fallback */
                speakViaWebSpeech(text, lang, opts);
            });
        }
    }

    /* ── Web Speech API fallback ── */
    var _supported = ('speechSynthesis' in root) && ('SpeechSynthesisUtterance' in root);
    var _cachedVoices = {};

    function findVoice(langPrefix) {
        if (_cachedVoices[langPrefix]) return _cachedVoices[langPrefix];
        if (!_supported) return null;

        var voices = root.speechSynthesis.getVoices();
        if (!voices || voices.length === 0) return null;

        var bestMatch = null;
        var fallback = null;

        for (var i = 0; i < voices.length; i++) {
            var v = voices[i];
            var lang = (v.lang || '').replace('_', '-').toLowerCase();

            if (lang === langPrefix.toLowerCase()) {
                bestMatch = v;
                break;
            }
            if (lang.indexOf(langPrefix.toLowerCase()) === 0) {
                bestMatch = bestMatch || v;
            }
        }

        _cachedVoices[langPrefix] = bestMatch || fallback;
        return _cachedVoices[langPrefix];
    }

    function speakViaWebSpeech(text, lang, opts) {
        opts = opts || {};
        lang = lang || DEFAULT_LANG;
        
        if (!_supported) {
            if (typeof opts.onEnd === 'function') setTimeout(opts.onEnd, 100);
            return;
        }

        var synth = root.speechSynthesis;
        synth.cancel();

        setTimeout(function () {
            var utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = lang;
            utterance.rate = 0.75;
            utterance.pitch = 1.15;
            utterance.volume = 1.0;

            var voice = findVoice(lang);
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
            _cachedVoices = {};
        });
    }

    /* ── Main API ── */
    function speak(text, lang, opts) {
        if (!text) return;
        speakViaGoogle(text, lang, opts);
    }

    function speakChinese(text, opts) {
        speak(text, 'zh-CN', opts);
    }

    function speakEnglish(text, opts) {
        speak(text, 'en-US', opts);
    }

    /* ── Auto-speak helper ── */
    function autoSpeak(text, lang) {
        if (!text) return;
        setTimeout(function () {
            speak(text, lang);
        }, 500);
    }

    /* ── Expose on window ── */
    root.SkoolTTS = {
        speak: speak,
        speakChinese: speakChinese,
        speakEnglish: speakEnglish,
        autoSpeak: autoSpeak,
        isSupported: function () { return true; }
    };

})(window);
