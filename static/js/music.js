/* ================================================================
   Skool — Background Music & Sound Effects
   Plays real MP3 background music tracks (royalty-free from Mixkit)
   and uses Web Audio API for short sound effects only.

   Usage:
     SkoolMusic.startBGM()      — start background music
     SkoolMusic.stopBGM()       — stop background music
     SkoolMusic.toggleMute()    — toggle mute state
     SkoolMusic.playCorrect()   — play "correct answer" jingle
     SkoolMusic.playWrong()     — play "wrong answer" sound
     SkoolMusic.playFinish()    — play "race complete" fanfare
     SkoolMusic.isMuted         — current mute state
   ================================================================ */

(function (root) {
    'use strict';

    /* ── State ── */
    var isMuted = false;
    var bgmStarted = false;
    var bgmAudio = null;
    var ctx = null;
    var masterGain = null;

    /* ── MP3 tracks (royalty-free, Mixkit License) ── */
    var TRACKS = [
        '/static/music/feeling-happy.mp3',
        '/static/music/playground-fun.mp3',
        '/static/music/dance-with-me.mp3',
        '/static/music/smile.mp3',
        '/static/music/jumping-around.mp3',
    ];

    /* ── Web Audio context (for SFX only) ── */
    function getCtx() {
        if (!ctx) {
            ctx = new (root.AudioContext || root.webkitAudioContext)();
            masterGain = ctx.createGain();
            masterGain.gain.value = 0.35;
            masterGain.connect(ctx.destination);
        }
        if (ctx.state === 'suspended') {
            ctx.resume();
        }
        return ctx;
    }

    /* ── Tone helper (for SFX only) ── */
    function playTone(freq, startTime, duration, dest, vol, type) {
        var c = getCtx();
        var t = type || 'sine';

        var osc1 = c.createOscillator();
        osc1.type = t;
        osc1.frequency.value = freq;

        var osc2 = c.createOscillator();
        osc2.type = 'sine';
        osc2.frequency.value = freq * 2;

        var env1 = c.createGain();
        var v = vol || 0.12;
        env1.gain.setValueAtTime(0, startTime);
        env1.gain.linearRampToValueAtTime(v, startTime + 0.015);
        env1.gain.exponentialRampToValueAtTime(v * 0.4, startTime + duration * 0.3);
        env1.gain.exponentialRampToValueAtTime(0.001, startTime + duration);

        var env2 = c.createGain();
        env2.gain.setValueAtTime(0, startTime);
        env2.gain.linearRampToValueAtTime(v * 0.15, startTime + 0.01);
        env2.gain.exponentialRampToValueAtTime(0.001, startTime + duration * 0.6);

        osc1.connect(env1);
        env1.connect(dest || masterGain);
        osc2.connect(env2);
        env2.connect(dest || masterGain);

        osc1.start(startTime);
        osc1.stop(startTime + duration + 0.05);
        osc2.start(startTime);
        osc2.stop(startTime + duration + 0.05);
    }

    function playPad(freqs, startTime, duration, dest, vol) {
        var c = getCtx();
        var v = vol || 0.03;
        freqs.forEach(function (freq) {
            var osc = c.createOscillator();
            osc.type = 'sine';
            osc.frequency.value = freq;
            var env = c.createGain();
            env.gain.setValueAtTime(0, startTime);
            env.gain.linearRampToValueAtTime(v, startTime + 0.3);
            env.gain.setValueAtTime(v, startTime + duration - 0.4);
            env.gain.linearRampToValueAtTime(0, startTime + duration);
            osc.connect(env);
            env.connect(dest || masterGain);
            osc.start(startTime);
            osc.stop(startTime + duration + 0.1);
        });
    }

    /* ── Background Music (real MP3) ── */

    function pickTrack() {
        return TRACKS[Math.floor(Math.random() * TRACKS.length)];
    }

    function startBGM() {
        if (bgmStarted) return;
        bgmStarted = true;

        if (!bgmAudio) {
            bgmAudio = new Audio();
            bgmAudio.loop = true;
            bgmAudio.volume = 0.3;
            bgmAudio.src = pickTrack();
        }

        if (isMuted) return;

        var p = bgmAudio.play();
        if (p && p.catch) {
            p.catch(function () {
                /* Autoplay blocked — will retry on interaction */
            });
        }
    }

    function stopBGM() {
        bgmStarted = false;
        if (bgmAudio) {
            bgmAudio.pause();
        }
    }

    function toggleMute() {
        isMuted = !isMuted;

        if (bgmAudio) {
            if (isMuted) {
                bgmAudio.pause();
            } else if (bgmStarted) {
                bgmAudio.play().catch(function () {});
            }
        }

        if (masterGain) {
            masterGain.gain.value = isMuted ? 0 : 0.35;
        }

        return isMuted;
    }

    /* ── Sound Effects (Web Audio — short jingles are fine) ── */

    function playCorrect() {
        if (isMuted) return;
        var c = getCtx();
        var sfx = c.createGain();
        sfx.gain.value = 0.4;
        sfx.connect(c.destination);
        var now = c.currentTime;
        playTone(523,  now,        0.18, sfx, 0.3);
        playTone(659,  now + 0.10, 0.18, sfx, 0.3);
        playTone(784,  now + 0.20, 0.22, sfx, 0.35);
        playTone(1047, now + 0.32, 0.35, sfx, 0.25);
    }

    function playWrong() {
        if (isMuted) return;
        var c = getCtx();
        var sfx = c.createGain();
        sfx.gain.value = 0.25;
        sfx.connect(c.destination);
        var now = c.currentTime;
        playTone(330, now,       0.25, sfx, 0.18, 'triangle');
        playTone(262, now + 0.2, 0.35, sfx, 0.15, 'triangle');
    }

    function playFinish() {
        if (isMuted) return;
        var c = getCtx();
        var sfx = c.createGain();
        sfx.gain.value = 0.4;
        sfx.connect(c.destination);
        var now = c.currentTime;
        playTone(392,  now,        0.18, sfx, 0.25);
        playTone(523,  now + 0.15, 0.18, sfx, 0.28);
        playTone(659,  now + 0.30, 0.18, sfx, 0.3);
        playTone(784,  now + 0.45, 0.22, sfx, 0.32);
        playTone(1047, now + 0.60, 0.6,  sfx, 0.35);
        playPad([1047, 1319, 1568], now + 0.75, 0.8, sfx, 0.06);
    }

    /* ── Auto-start on first user interaction (iOS requirement) ── */
    var _interacted = false;
    function onFirstInteraction() {
        if (_interacted) return;
        _interacted = true;
        startBGM();
        document.removeEventListener('touchstart', onFirstInteraction);
        document.removeEventListener('click', onFirstInteraction);
    }
    document.addEventListener('touchstart', onFirstInteraction, { once: true });
    document.addEventListener('click', onFirstInteraction, { once: true });

    /* ── Public API ── */
    root.SkoolMusic = {
        startBGM: startBGM,
        stopBGM: stopBGM,
        toggleMute: toggleMute,
        playCorrect: playCorrect,
        playWrong: playWrong,
        playFinish: playFinish,
        pickRandomMood: function () { /* kept for compatibility */
            if (bgmAudio) bgmAudio.src = pickTrack();
        },
        get isMuted() { return isMuted; }
    };

})(window);
