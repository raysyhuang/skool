/* ================================================================
   Skool -- Racing Game Logic
   Manages the 5-question Chinese character racing game.

   Dependencies (must be loaded before this script):
     - /static/js/common.js   (SkoolAPI)
     - /static/js/tts.js      (SkoolTTS)

   Expects the template to set these globals:
     window.questionsData   = [ { id, question_number, character, pinyin,
                                   meaning, image_url, options, correct_answer,
                                   mode, shown_meaning, display_word, meaning_hint }, ... ]
     window.sessionId       = <int>
     window.totalQuestions   = <int>          (typically 5)
     window.initialPoints   = <int>          (user's current points total)
   ================================================================ */

(function (root) {
    'use strict';

    /* ──────────────────────────────────────────────
       Validate prerequisites
       ────────────────────────────────────────────── */

    if (!root.SkoolAPI) {
        console.error('[RacingGame] common.js (SkoolAPI) must be loaded first.');
        return;
    }
    if (!root.SkoolTTS) {
        console.error('[RacingGame] tts.js (SkoolTTS) must be loaded first.');
        return;
    }


    /* ──────────────────────────────────────────────
       Read globals set by the Jinja template
       ────────────────────────────────────────────── */

    var questions      = root.questionsData   || [];
    var sessionId      = root.sessionId       || 0;
    var totalQuestions  = root.totalQuestions  || questions.length || 5;
    var points         = root.initialPoints   || 0;


    /* ──────────────────────────────────────────────
       Game state
       ────────────────────────────────────────────── */

    var currentIndex = 0;       /* index into questions[] */
    var answering    = false;   /* lock to prevent double-tap */


    /* ──────────────────────────────────────────────
       DOM references (cached once on init)
       ────────────────────────────────────────────── */

    var charDisplay, pinyinDisplay, optionsRow, progressLabel,
        pointsDisplay, carSprite, feedbackOverlay, feedbackMsg,
        stopFlags, celebrationBurst, screenFlash, progressBarFill;


    function cacheDom() {
        charDisplay       = document.getElementById('charDisplay');
        pinyinDisplay     = document.getElementById('pinyinDisplay');
        optionsRow        = document.getElementById('optionsRow');
        progressLabel     = document.getElementById('progressLabel');
        pointsDisplay     = document.getElementById('pointsDisplay');
        carSprite         = document.getElementById('carSprite');
        feedbackOverlay   = document.getElementById('feedbackOverlay');
        feedbackMsg       = document.getElementById('feedbackMsg');
        celebrationBurst  = document.getElementById('celebrationBurst');
        screenFlash       = document.getElementById('screenFlash');
        progressBarFill   = document.getElementById('progressBarFill');
        stopFlags         = document.querySelectorAll('.stop-flag');
    }


    /* ──────────────────────────────────────────────
       Background theme rotation
       ────────────────────────────────────────────── */

    var BG_THEMES = ['bg-highway', 'bg-city', 'bg-beach', 'bg-space', 'bg-forest', 'bg-snow'];

    function applyRandomBackground() {
        var questionArea = document.querySelector('.question-area');
        if (!questionArea) return;
        var theme = BG_THEMES[Math.floor(Math.random() * BG_THEMES.length)];
        questionArea.classList.add(theme);
    }


    /* ──────────────────────────────────────────────
       Render a question
       ────────────────────────────────────────────── */

    function renderQuestion(idx) {
        var q = questions[idx];
        if (!q) return;

        var mode = q.mode || 'char_to_image';
        answering = false;

        /* -- Prompt area (character display + pinyin) -- */
        if (charDisplay) {
            charDisplay.style.animation = 'none';
            void charDisplay.offsetWidth;
            charDisplay.style.animation = 'charPop 0.4s ease-out';

            /* Reset styles */
            charDisplay.style.fontSize = '';
            charDisplay.style.textTransform = '';
            charDisplay.innerHTML = '';

            if (mode === 'image_to_char') {
                /* Show the image as the prompt */
                charDisplay.innerHTML = '<img src="' + q.image_url + '" alt="' + q.meaning + '" style="width:clamp(80px,14vw,140px);height:clamp(80px,14vw,140px);object-fit:contain;">';
            } else if (mode === 'meaning_to_char') {
                /* Show the English word as the prompt */
                charDisplay.textContent = q.meaning;
                charDisplay.style.fontSize = 'clamp(40px, 8vw, 80px)';
                charDisplay.style.textTransform = 'capitalize';
            } else if (mode === 'true_or_false') {
                /* Show character + meaning underneath */
                charDisplay.textContent = q.character;
            } else if (mode === 'fill_in_blank') {
                /* Show word with blank */
                charDisplay.textContent = q.display_word || q.character;
                charDisplay.style.fontSize = 'clamp(60px, 12vw, 120px)';
            } else if (mode === 'pinyin_to_char') {
                /* Show pinyin as prompt */
                charDisplay.textContent = q.pinyin;
                charDisplay.style.fontSize = 'clamp(48px, 10vw, 96px)';
            } else {
                /* Default: show Chinese character */
                charDisplay.textContent = q.character;
            }
        }

        if (pinyinDisplay) {
            if (mode === 'image_to_char' || mode === 'meaning_to_char' || mode === 'pinyin_to_char') {
                /* Hide pinyin — it's the clue or already shown */
                pinyinDisplay.textContent = '';
            } else if (mode === 'true_or_false') {
                /* Show image if available (for young kids), otherwise text meaning */
                if (q.shown_image) {
                    pinyinDisplay.innerHTML = '<img src="' + q.shown_image + '" style="width:clamp(80px,18vw,140px);height:auto;margin-top:8px;" alt="?">';
                } else {
                    pinyinDisplay.innerHTML = '<span style="font-size:clamp(20px,4vw,32px);color:#636e72;">' + q.pinyin + '</span>' +
                        '<br><span style="font-size:clamp(28px,5vw,44px);font-weight:800;color:#2d3436;text-transform:capitalize;">= "' + (q.shown_meaning || q.meaning) + '"</span>';
                }
            } else if (mode === 'fill_in_blank') {
                /* Show meaning hint */
                pinyinDisplay.innerHTML = '<span style="font-size:clamp(20px,4vw,32px);color:#636e72;">(' + (q.meaning_hint || q.meaning) + ')</span>';
            } else {
                pinyinDisplay.innerHTML = '';
                pinyinDisplay.textContent = q.pinyin;
            }
        }

        /* -- Progress label -- */
        if (progressLabel) {
            progressLabel.textContent = 'Stop ' + q.question_number + ' of ' + totalQuestions;
        }

        /* -- Progress bar -- */
        if (progressBarFill) {
            var pct = (idx / totalQuestions) * 100;
            progressBarFill.style.width = pct + '%';
        }

        /* -- Stop flags -- */
        if (stopFlags && stopFlags.length) {
            for (var f = 0; f < stopFlags.length; f++) {
                stopFlags[f].classList.remove('reached', 'current');
                if (f < idx)       stopFlags[f].classList.add('reached');
                else if (f === idx) stopFlags[f].classList.add('current');
            }
        }

        /* -- Build option buttons -- */
        if (optionsRow) {
            optionsRow.innerHTML = '';

            if (mode === 'true_or_false') {
                /* Special: two big True / False buttons */
                _buildTrueFalseButtons(q);
            } else {
                /* Standard option buttons */
                q.options.forEach(function (opt) {
                    var btn = document.createElement('button');
                    btn.className = 'option-btn';
                    btn.type = 'button';
                    btn.dataset.answer = opt;

                    /* Tap handler */
                    btn.addEventListener('touchend', handleOptionTap, { passive: false });
                    btn.addEventListener('click', handleOptionClick);

                    /* Content depends on what the options represent */
                    if (/^(\/|https?:\/\/)/.test(opt)) {
                        /* Image option */
                        var img = document.createElement('img');
                        img.src = opt;
                        img.alt = 'option';
                        img.draggable = false;
                        btn.appendChild(img);
                    } else {
                        var span = document.createElement('span');
                        span.className = 'option-label';
                        /* Chinese character options get bigger font */
                        if (mode === 'image_to_char' || mode === 'meaning_to_char' ||
                            mode === 'pinyin_to_char' || mode === 'fill_in_blank') {
                            span.style.fontSize = 'clamp(32px, 6vw, 52px)';
                        }
                        span.textContent = opt;
                        btn.appendChild(span);
                    }

                    optionsRow.appendChild(btn);
                });
            }
        }

        /* -- Auto TTS -- */
        setTimeout(function () {
            if (mode === 'image_to_char' || mode === 'meaning_to_char' || mode === 'pinyin_to_char') {
                /* Don't speak — let them figure it out */
            } else {
                root.SkoolTTS.speakChinese(q.character);
            }
        }, 300);
    }


    /* ──────────────────────────────────────────────
       True/False button builder
       ────────────────────────────────────────────── */

    function _buildTrueFalseButtons(q) {
        var trueBtn = document.createElement('button');
        trueBtn.className = 'option-btn tf-btn tf-true';
        trueBtn.type = 'button';
        trueBtn.dataset.answer = 'true';
        trueBtn.innerHTML = '<span class="option-label" style="font-size:clamp(28px,5vw,44px);">\u2705 True!</span>';
        trueBtn.addEventListener('touchend', handleOptionTap, { passive: false });
        trueBtn.addEventListener('click', handleOptionClick);

        var falseBtn = document.createElement('button');
        falseBtn.className = 'option-btn tf-btn tf-false';
        falseBtn.type = 'button';
        falseBtn.dataset.answer = 'false';
        falseBtn.innerHTML = '<span class="option-label" style="font-size:clamp(28px,5vw,44px);">\u274C False!</span>';
        falseBtn.addEventListener('touchend', handleOptionTap, { passive: false });
        falseBtn.addEventListener('click', handleOptionClick);

        optionsRow.appendChild(trueBtn);
        optionsRow.appendChild(falseBtn);
    }


    /* ──────────────────────────────────────────────
       Option tap handling (de-duped for touch+click)
       ────────────────────────────────────────────── */

    var _lastTapTime = 0;

    /**
     * Touch handler -- preferred on iPad.
     * We call preventDefault to suppress the follow-up click event.
     */
    function handleOptionTap(e) {
        e.preventDefault();
        var btn = findOptionBtn(e.target);
        if (btn) selectAnswer(btn);
    }

    /**
     * Click handler -- fallback for non-touch.
     * Ignored if a touch already fired very recently.
     */
    function handleOptionClick(e) {
        if (Date.now() - _lastTapTime < 500) return;
        var btn = findOptionBtn(e.target);
        if (btn) selectAnswer(btn);
    }

    /** Walk up the DOM to find the .option-btn ancestor. */
    function findOptionBtn(el) {
        while (el && !el.classList.contains('option-btn')) {
            el = el.parentElement;
        }
        return el;
    }


    /* ──────────────────────────────────────────────
       Submit an answer
       ────────────────────────────────────────────── */

    /* Track whether the API was already called for this question (first attempt only) */
    var apiCalledForQuestion = {};

    function selectAnswer(btn) {
        if (answering) return;          /* block double-tap */
        answering = true;
        _lastTapTime = Date.now();

        var selected = btn.dataset.answer;
        var q = questions[currentIndex];
        var isCorrect = (selected === q.correct_answer);
        var isFirstAttempt = !apiCalledForQuestion[q.id];

        /* Disable all buttons immediately */
        var allBtns = optionsRow.querySelectorAll('.option-btn');
        for (var i = 0; i < allBtns.length; i++) {
            allBtns[i].classList.add('disabled');
        }

        /* Only call API on first attempt (scoring happens server-side once) */
        var apiPromise;
        if (isFirstAttempt) {
            apiCalledForQuestion[q.id] = true;
            apiPromise = root.SkoolAPI.postAnswer(q.id, selected);
        } else {
            apiPromise = Promise.resolve({ is_correct: isCorrect, points_earned: 0 });
        }

        apiPromise
            .then(function (data) {

                /* ── Sound effects ── */
                if (root.SkoolMusic) {
                    if (isCorrect) root.SkoolMusic.playCorrect();
                    else root.SkoolMusic.playWrong();
                }

                if (isCorrect) {
                    /* ═══ CORRECT ═══ */

                    /* Highlight correct button */
                    btn.classList.add('correct');

                    /* Update points (only meaningful on first attempt) */
                    points += (data.points_earned || 0);
                    if (pointsDisplay) {
                        pointsDisplay.textContent = points;
                        pointsDisplay.style.transform = 'scale(1.3)';
                        setTimeout(function () {
                            pointsDisplay.style.transform = 'scale(1)';
                        }, 250);
                    }

                    triggerCarBoost();
                    showFeedback(true);
                    showScreenFlash('correct');
                    spawnConfetti(10);

                    /* Move car forward */
                    moveCarToStop(currentIndex + 1);

                    /* Update progress bar */
                    if (progressBarFill) {
                        var pct = ((currentIndex + 1) / totalQuestions) * 100;
                        progressBarFill.style.width = pct + '%';
                    }

                    /* Advance to next question */
                    setTimeout(function () {
                        currentIndex++;
                        if (currentIndex < totalQuestions) {
                            renderQuestion(currentIndex);
                        } else {
                            finishRace();
                        }
                    }, 1600);

                } else {
                    /* ═══ WRONG — Teaching moment + retry ═══ */

                    /* Mark wrong button red */
                    btn.classList.add('wrong');

                    /* Highlight the correct answer with a glow so they can see it */
                    for (var j = 0; j < allBtns.length; j++) {
                        if (allBtns[j].dataset.answer === q.correct_answer) {
                            allBtns[j].classList.add('correct');
                        }
                    }

                    triggerCarShake();
                    showScreenFlash('wrong');

                    /* Show teaching panel */
                    showTeachingPanel(q);

                    /* After teaching panel is dismissed, let them retry */
                }
            })
            .catch(function (err) {
                console.error('[RacingGame] Answer error:', err);
                answering = false;
                for (var k = 0; k < allBtns.length; k++) {
                    allBtns[k].classList.remove('disabled');
                }
            });
    }


    /* ──────────────────────────────────────────────
       Teaching panel (shown on wrong answer)
       ────────────────────────────────────────────── */

    function showTeachingPanel(q) {
        var panel = document.getElementById('teachingPanel');
        if (!panel) return;

        /* Fill in the teaching content */
        var tChar = document.getElementById('teachChar');
        var tPinyin = document.getElementById('teachPinyin');
        var tMeaning = document.getElementById('teachMeaning');
        var tImage = document.getElementById('teachImage');
        var tBtn = document.getElementById('teachGotIt');

        if (tChar) tChar.textContent = q.character;
        if (tPinyin) tPinyin.textContent = q.pinyin;
        if (tMeaning) tMeaning.textContent = q.meaning;
        if (tImage) {
            if (q.image_url) {
                tImage.innerHTML = '<img src="' + q.image_url + '" alt="' + q.meaning + '">';
            } else {
                tImage.textContent = q.meaning;
            }
        }

        /* Speak the character */
        root.SkoolTTS.speakChinese(q.character);

        /* Show panel */
        panel.classList.add('active');

        /* "Got it!" button → re-render question for retry (wrong options removed) */
        function onGotIt(e) {
            e.preventDefault();
            panel.classList.remove('active');
            tBtn.removeEventListener('click', onGotIt);
            tBtn.removeEventListener('touchend', onGotIt);

            /* Re-render the same question for retry */
            renderQuestion(currentIndex);
        }

        tBtn.addEventListener('click', onGotIt);
        tBtn.addEventListener('touchend', onGotIt, { passive: false });
    }


    /* ──────────────────────────────────────────────
       Car movement
       ────────────────────────────────────────────── */

    /**
     * Car position is a percentage of road width.
     * 6 stops (0-5 answered) map to: 4%, 20.8%, 37.6%, 54.4%, 71.2%, 88%
     * Formula: (stopIndex / totalQuestions * 84) + 4
     */
    function moveCarToStop(stopIndex) {
        if (!carSprite) return;
        var pct = (stopIndex / totalQuestions * 84) + 4;
        carSprite.style.left = pct + '%';
    }

    function triggerCarBoost() {
        if (!carSprite) return;
        carSprite.classList.remove('boost', 'shake', 'spin');
        void carSprite.offsetWidth;     /* force reflow */
        carSprite.classList.add('boost');
        carSprite.addEventListener('animationend', function handler() {
            carSprite.classList.remove('boost');
            carSprite.removeEventListener('animationend', handler);
        });
    }

    function triggerCarShake() {
        if (!carSprite) return;
        carSprite.classList.remove('boost', 'shake', 'spin');
        void carSprite.offsetWidth;
        carSprite.classList.add('shake');
        carSprite.addEventListener('animationend', function handler() {
            carSprite.classList.remove('shake');
            carSprite.removeEventListener('animationend', handler);
        });
    }


    /* ──────────────────────────────────────────────
       Feedback overlay  (big text: "great!" / "try again")
       ────────────────────────────────────────────── */

    function showFeedback(correct) {
        if (!feedbackOverlay || !feedbackMsg) return;

        feedbackMsg.textContent = correct ? '\uD83C\uDF89 \u68D2\uFF01' : '\uD83E\uDD14 \u518D\u8BD5\u8BD5';
        feedbackMsg.className   = 'feedback-msg ' + (correct ? 'correct' : 'wrong');

        feedbackOverlay.classList.add('active');
        setTimeout(function () {
            feedbackOverlay.classList.remove('active');
        }, 1200);
    }


    /* ──────────────────────────────────────────────
       Screen flash (green / red)
       ────────────────────────────────────────────── */

    function showScreenFlash(type) {
        if (!screenFlash) return;
        screenFlash.className = 'screen-flash ' + type + '-flash active';
        setTimeout(function () {
            screenFlash.classList.remove('active');
        }, 600);
    }


    /* ──────────────────────────────────────────────
       Confetti burst
       ────────────────────────────────────────────── */

    var CONFETTI_COLORS = [
        '#ff6b35', '#fdcb6e', '#00b894', '#e84393',
        '#6c5ce7', '#74b9ff', '#fd79a8', '#ffeaa7'
    ];

    function spawnConfetti(count) {
        if (!celebrationBurst) return;

        celebrationBurst.classList.add('active');
        celebrationBurst.innerHTML = '';

        for (var i = 0; i < count; i++) {
            var piece = document.createElement('div');
            piece.className = 'confetti-piece';
            piece.style.left = (Math.random() * 100) + '%';
            piece.style.top = '-20px';
            piece.style.background = CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)];
            piece.style.animationDelay = (Math.random() * 0.4) + 's';
            piece.style.animationDuration = (1.5 + Math.random()) + 's';
            piece.style.width = (8 + Math.random() * 8) + 'px';
            piece.style.height = (8 + Math.random() * 8) + 'px';
            piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
            celebrationBurst.appendChild(piece);
        }

        setTimeout(function () {
            celebrationBurst.classList.remove('active');
            celebrationBurst.innerHTML = '';
        }, 2500);
    }

    /** Big celebration at end of race */
    function spawnBigCelebration() {
        if (!celebrationBurst) return;

        celebrationBurst.classList.add('active');
        celebrationBurst.innerHTML = '';

        for (var i = 0; i < 50; i++) {
            var piece = document.createElement('div');
            piece.className = 'confetti-piece big';
            piece.style.left = (Math.random() * 100) + '%';
            piece.style.top = '-30px';
            piece.style.background = CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)];
            piece.style.animationDelay = (Math.random() * 1.5) + 's';
            piece.style.animationDuration = (2 + Math.random() * 2) + 's';
            piece.style.width = (10 + Math.random() * 12) + 'px';
            piece.style.height = (10 + Math.random() * 12) + 'px';
            piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '3px';
            celebrationBurst.appendChild(piece);
        }

        /* Don't clear -- we redirect shortly */
    }


    /* ──────────────────────────────────────────────
       Finish the race (all 5 questions done)
       ────────────────────────────────────────────── */

    function finishRace() {
        /* Big celebration */
        spawnBigCelebration();

        /* Victory fanfare */
        if (root.SkoolMusic) root.SkoolMusic.playFinish();

        /* Speak congratulation */
        root.SkoolTTS.speakChinese('\u592A\u68D2\u4E86');    /* "tai bang le!" */

        /* Call complete API, then redirect */
        root.SkoolAPI.completeSession(sessionId)
            .then(function () {
                setTimeout(function () {
                    root.location.href = '/game/session-complete/' + sessionId;
                }, 2200);
            })
            .catch(function (err) {
                console.error('[RacingGame] Complete error:', err);
                /* Redirect anyway so the child isn't stuck */
                setTimeout(function () {
                    root.location.href = '/game/session-complete/' + sessionId;
                }, 2200);
            });
    }


    /* ──────────────────────────────────────────────
       TTS button handler (exposed globally for onclick)
       ────────────────────────────────────────────── */

    root.speakCharacter = function () {
        var q = questions[currentIndex];
        if (q) {
            root.SkoolTTS.speakChinese(q.character);
        }
    };

    root.toggleMusic = function () {
        if (!root.SkoolMusic) return;
        var muted = root.SkoolMusic.toggleMute();
        var btn = document.getElementById('musicToggle');
        if (btn) btn.classList.toggle('muted', muted);
    };


    /* ──────────────────────────────────────────────
       Initialise
       ────────────────────────────────────────────── */

    function init() {
        cacheDom();

        if (!questions || questions.length === 0) {
            console.error('[RacingGame] No questions data. Set window.questionsData before loading racing.js.');
            return;
        }

        /* Apply random background theme */
        applyRandomBackground();

        /* Tell music.js to pick a random mood */
        if (root.SkoolMusic && root.SkoolMusic.pickRandomMood) {
            root.SkoolMusic.pickRandomMood();
        }

        /* Set initial car position */
        moveCarToStop(0);

        /* Render first question */
        renderQuestion(0);

        /* Auto-speak the first character (handles iOS gesture requirement) */
        root.SkoolTTS.autoSpeak(questions[0].character);
    }

    /* Wait for DOM */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})(window);
