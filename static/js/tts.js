/* ================================================================
   Skool -- Text-to-Speech Wrapper
   Plays neural voices from our /game/tts endpoint (edge-tts).
   Falls back to the Web Speech API only if the server audio fails.
   ================================================================ */

(function (root) {
    'use strict';

    /* ── Configuration ── */
    var DEFAULT_LANG = 'zh-CN';

    /* ── Server neural TTS ── */
    var _ttsAudio = null;

    /* ── Duck background music while speaking ── */
    function _duck() {
        if (root.SkoolMusic && root.SkoolMusic.duck) root.SkoolMusic.duck();
    }

    function _unduck() {
        if (root.SkoolMusic && root.SkoolMusic.unduck) root.SkoolMusic.unduck();
    }

    /*
     * One reusable <audio> element, unlocked on the first tap.
     *
     * iPad Safari only lets an audio element play outside a user gesture
     * once that same element has played inside one. A fresh `new Audio()`
     * per word is never unlocked, so every auto-read was rejected and fell
     * back to the robotic Web Speech voice. We unlock one element on the
     * first touch (with a silent clip) and swap its src for each word.
     */
    var SILENCE_URL = '/static/music/silence.mp3';
    var _unlocked = false;

    function _audioEl() {
        if (!_ttsAudio) {
            _ttsAudio = new Audio();
            _ttsAudio.preload = 'auto';
        }
        return _ttsAudio;
    }

    function _unlock() {
        if (_unlocked) return;
        var el = _audioEl();
        if (el.src && !el.paused) { _unlocked = true; return; }  /* already speaking from a tap */
        el.onended = null;  /* the last word's handlers must not fire for the silence */
        el.onerror = null;
        el.src = SILENCE_URL;
        var p = el.play();
        if (p && p.then) {
            p.then(function () { _unlocked = true; }).catch(function () {});
        } else {
            _unlocked = true;
        }
    }

    ['touchend', 'pointerup', 'click', 'keydown'].forEach(function (evt) {
        root.addEventListener(evt, _unlock, { capture: true, passive: true });
    });

    function speakViaServer(text, lang, opts) {
        opts = opts || {};
        lang = lang || DEFAULT_LANG;

        var el = _audioEl();
        el.pause();
        el.src = '/game/tts?text=' + encodeURIComponent(text) + '&lang=' + encodeURIComponent(lang);
        el.volume = 1.0;

        el.onended = function () {
            _unduck();
            if (typeof opts.onEnd === 'function') opts.onEnd();
        };

        el.onerror = function () {
            /* Server/network failure: robotic voice beats silence here */
            console.warn('[Skool TTS] Server TTS failed, falling back to Web Speech API.');
            _unduck();
            speakViaWebSpeech(text, lang, opts);
        };

        _duck();
        var p = el.play();
        if (p && p.then) p.then(function () { _unlocked = true; }, function () {});
        if (p && p.catch) {
            p.catch(function (err) {
                _unduck();
                if (err && err.name === 'NotAllowedError') {
                    /* Not unlocked yet (no tap so far). Stay quiet rather than
                       switch to the robot voice; the 🔊 button works on tap. */
                    return;
                }
                if (err && err.name === 'AbortError') return;  /* replaced by a newer word */
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
                _unduck();
                if (typeof opts.onEnd === 'function') opts.onEnd();
            };
            utterance.onerror = function () {
                clearInterval(keepAlive);
                _unduck();
            };

            _duck();
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
        speakViaServer(text, lang, opts);
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
