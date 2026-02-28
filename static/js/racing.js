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
    var gameType       = root.gameType        || 'chinese';


    /* ──────────────────────────────────────────────
       Game state
       ────────────────────────────────────────────── */

    var currentIndex = 0;       /* index into questions[] */
    var answering    = false;   /* lock to prevent double-tap */
    var carLevel     = root.carLevel || 0;


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

        /* Record question start time for speed bonus */
        root.SkoolAPI.apiFetch('/game/start-question/' + q.id, { method: 'POST' }).catch(function() {});

        /* ── 3-Step Learning Flow for low-mastery Chinese chars ── */
        if (gameType === 'chinese' && q.mastery !== undefined && q.mastery < 2) {
            _showLearningStep(q, function() {
                _renderQuestionInner(idx);
            });
            return;
        }

        _renderQuestionInner(idx);
    }


    /* ──────────────────────────────────────────────
       3-Step Learning Flow (Chinese low-mastery)
       ────────────────────────────────────────────── */

    function _showLearningStep(q, onDone) {
        var panel = document.getElementById('teachingPanel');
        if (!panel) { onDone(); return; }

        var tChar = document.getElementById('teachChar');
        var tPinyin = document.getElementById('teachPinyin');
        var tMeaning = document.getElementById('teachMeaning');
        var tImage = document.getElementById('teachImage');
        var tArrow = document.querySelector('.teaching-arrow');
        var tBtn = document.getElementById('teachGotIt');
        var header = panel.querySelector('.teaching-header');

        if (header) header.textContent = 'Let\'s learn! \uD83D\uDCDA';

        if (tChar) tChar.textContent = q.character;
        if (tPinyin) tPinyin.textContent = q.pinyin;
        if (tMeaning) tMeaning.textContent = q.meaning;
        if (tImage) tImage.style.display = 'none';
        if (tArrow) tArrow.style.display = 'none';
        if (tBtn) tBtn.textContent = '\u25B6 Ready!';

        /* Auto-speak */
        root.SkoolTTS.speakChinese(q.character);

        /* Show Hanzi Writer if available */
        var hanziContainer = document.getElementById('hanziWriterLearn');
        if (!hanziContainer) {
            hanziContainer = document.createElement('div');
            hanziContainer.id = 'hanziWriterLearn';
            hanziContainer.style.cssText = 'width:120px;height:120px;margin:8px auto;';
            var body = panel.querySelector('.teaching-body');
            if (body) body.appendChild(hanziContainer);
        }
        hanziContainer.innerHTML = '';
        hanziContainer.style.display = 'block';

        if (root.HanziWriter && q.character && q.character.length === 1) {
            try {
                var writer = root.HanziWriter.create(hanziContainer, q.character, {
                    width: 120, height: 120,
                    padding: 5,
                    strokeAnimationSpeed: 1,
                    delayBetweenStrokes: 200,
                    showOutline: true,
                });
                writer.animateCharacter();
            } catch(e) { /* Hanzi Writer may not support all chars */ }
        }

        panel.classList.add('active');

        function onReady(e) {
            e.preventDefault();
            panel.classList.remove('active');
            tBtn.removeEventListener('click', onReady);
            tBtn.removeEventListener('touchend', onReady);
            if (header) header.textContent = 'Hmm, not quite! \uD83E\uDD14';
            if (tBtn) tBtn.textContent = '\uD83D\uDCAA Try again!';
            hanziContainer.style.display = 'none';
            if (tImage) tImage.style.display = '';
            if (tArrow) tArrow.style.display = '';
            onDone();
        }
        tBtn.addEventListener('click', onReady);
        tBtn.addEventListener('touchend', onReady, { passive: false });
    }


    function _renderQuestionInner(idx) {
        var q = questions[idx];
        if (!q) return;

        var mode = q.mode || 'char_to_image';

        /* -- Prompt area (character display + pinyin) -- */
        var isMathLogic = (gameType === 'math' || gameType === 'logic' || gameType === 'english');

        if (charDisplay) {
            charDisplay.style.animation = 'none';
            void charDisplay.offsetWidth;
            charDisplay.style.animation = 'charPop 0.4s ease-out';

            /* Reset styles */
            charDisplay.style.fontSize = '';
            charDisplay.style.textTransform = '';
            charDisplay.innerHTML = '';

            if (isMathLogic) {
                /* Math/Logic: show expression or emoji visual */
                var expr = q.expression || q.prompt_text || q.character || '';
                var img = q.prompt_image;
                if (img && /[\u{1F300}-\u{1FAFF}]/u.test(img)) {
                    /* Emoji visual (counting, patterns) */
                    charDisplay.innerHTML = '<span style="font-size:clamp(36px,7vw,64px);line-height:1.4;word-break:break-all;">' + img + '</span>';
                } else {
                    /* Text expression (arithmetic, analogies) */
                    charDisplay.textContent = expr;
                    charDisplay.style.fontSize = 'clamp(36px, 7vw, 72px)';
                }
            } else if (mode === 'image_to_char') {
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
            } else if (mode === 'audio_to_char') {
                /* Show a tappable speaker emoji — pure listening mode */
                charDisplay.innerHTML = '<span class="audio-speaker-btn" onclick="speakCharacter()" style="cursor:pointer;font-size:clamp(80px,16vw,140px);user-select:none;">\uD83D\uDD0A</span>';
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
            if (isMathLogic) {
                /* Show prompt text underneath expression */
                var pt = q.prompt_text || q.pinyin || '';
                pinyinDisplay.innerHTML = '<span style="font-size:clamp(20px,4vw,32px);color:#636e72;font-weight:600;">' + pt + '</span>';
            } else if (mode === 'image_to_char' || mode === 'meaning_to_char' || mode === 'pinyin_to_char' || mode === 'audio_to_char') {
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
                        /* Bigger font for character picks and math/logic */
                        if (isMathLogic || mode === 'image_to_char' || mode === 'meaning_to_char' ||
                            mode === 'pinyin_to_char' || mode === 'fill_in_blank' ||
                            mode === 'audio_to_char') {
                            span.style.fontSize = 'clamp(32px, 6vw, 52px)';
                        }
                        span.textContent = opt;
                        btn.appendChild(span);
                    }

                    optionsRow.appendChild(btn);
                });
            }
        }

        /* -- Auto TTS (skip for math/logic) -- */
        if (!isMathLogic) {
            setTimeout(function () {
                if (mode === 'image_to_char' || mode === 'meaning_to_char' || mode === 'pinyin_to_char') {
                    /* Don't speak — let them figure it out */
                } else {
                    root.SkoolTTS.speakChinese(q.character);
                }
            }, 300);
        }
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

    function selectAnswer(btn) {
        if (answering) return;          /* block double-tap */
        answering = true;
        _lastTapTime = Date.now();

        var selected = btn.dataset.answer;
        var q = questions[currentIndex];
        var isCorrect = (selected === q.correct_answer);

        /* Disable all buttons immediately */
        var allBtns = optionsRow.querySelectorAll('.option-btn');
        for (var i = 0; i < allBtns.length; i++) {
            allBtns[i].classList.add('disabled');
        }

        /* Call API for every attempt; backend handles scoring/state transitions. */
        var apiPromise = root.SkoolAPI.postAnswer(q.id, selected);

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

                    /* Update points earned on this attempt */
                    points += (data.points_earned || 0);
                    if (pointsDisplay) {
                        pointsDisplay.textContent = points;
                        pointsDisplay.style.transform = 'scale(1.3)';
                        setTimeout(function () {
                            pointsDisplay.style.transform = 'scale(1)';
                        }, 250);
                    }

                    /* Show bonus multiplier text */
                    if (data.bonus === 'lucky_star') {
                        showBonusText('\u2B50 LUCKY STAR! 3x! \u2B50');
                        spawnConfetti(25);
                    } else if (data.bonus === 'speed_bonus') {
                        showBonusText('\u26A1 SPEED BONUS!');
                        spawnConfetti(15);
                    } else {
                        spawnConfetti(10);
                    }

                    triggerCarBoost();
                    showFeedback(true);
                    showScreenFlash('correct');

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

                    triggerCarShake();
                    showScreenFlash('wrong');

                    /* Show hint panel (don't reveal the answer) */
                    showTeachingPanel(q);

                    /* After teaching panel is dismissed, let them retry */
                }
            })
            .catch(function (err) {
                console.error('[RacingGame] Answer error:', err);
                root.SkoolAPI.showError('Could not submit answer. Tap to retry.');
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

        /* Fill in hint content (don't reveal the answer!) */
        var tChar = document.getElementById('teachChar');
        var tPinyin = document.getElementById('teachPinyin');
        var tMeaning = document.getElementById('teachMeaning');
        var tImage = document.getElementById('teachImage');
        var tArrow = document.querySelector('.teaching-arrow');
        var tBtn = document.getElementById('teachGotIt');
        var mode = q.mode || '';

        /* Hide answer-revealing elements by default */
        if (tImage) tImage.style.display = 'none';
        if (tArrow) tArrow.style.display = 'none';

        if (gameType === 'math') {
            /* Math hints — encourage without revealing the answer */
            /* Parse operands from expression (e.g. "3 + 5 = ?") */
            var nums = (q.expression || '').match(/\d+/g) || [];
            var a = nums[0] || '';
            var b = nums[1] || '';

            if (tChar) tChar.textContent = '\uD83E\uDDEE';
            var mathHint = 'Try again carefully!';
            if (mode === 'counting') {
                mathHint = 'Count again carefully!';
            } else if (mode === 'addition_simple' || mode === 'addition_easy') {
                mathHint = 'Try counting up from ' + a + '!';
            } else if (mode === 'subtraction_simple' || mode === 'subtraction_easy') {
                mathHint = 'Try counting down from ' + a + '!';
            } else if (mode === 'multiplication_easy' || mode === 'multiplication_medium') {
                mathHint = 'Think: ' + a + ' groups of ' + b + '!';
            } else if (mode === 'missing_number_easy' || mode === 'missing_number_medium') {
                mathHint = 'What number makes it work?';
            } else if (mode === 'addition_medium') {
                mathHint = 'Break it into hundreds, tens, and ones!';
            } else if (mode === 'subtraction_medium') {
                mathHint = 'Break it into hundreds, tens, and ones!';
            } else if (mode === 'division_basic') {
                mathHint = 'How many groups of ' + b + ' fit in ' + a + '?';
            } else if (mode === 'fractions_compare') {
                mathHint = 'Think about slicing a pizza!';
            }
            if (tPinyin) tPinyin.textContent = mathHint;
            if (tMeaning) tMeaning.textContent = '';

        } else if (gameType === 'logic') {
            /* Logic hints — nudge toward the pattern */
            if (tChar) tChar.textContent = '\uD83E\uDDE9';
            var logicHint = 'Think carefully!';
            if (mode === 'pattern_next') {
                logicHint = 'Look at the pattern \u2014 what repeats?';
            } else if (mode === 'odd_one_out') {
                logicHint = 'Three are the same kind. One is different!';
            } else if (mode === 'size_order') {
                logicHint = 'Think about real life \u2014 which is the biggest?';
            } else if (mode === 'matching_pairs') {
                logicHint = 'What goes together?';
            } else if (mode === 'number_pattern') {
                logicHint = 'Look at the difference between each number!';
            } else if (mode === 'analogy') {
                logicHint = 'How are the first two words related?';
            } else if (mode === 'color_match') {
                logicHint = 'Look at the colors carefully!';
            } else if (mode === 'counting_objects') {
                logicHint = 'Count them one by one!';
            } else if (mode === 'sequence_completion') {
                logicHint = 'Look at the pattern \u2014 what comes next?';
            } else if (mode === 'comparison') {
                logicHint = 'Think about real life!';
            } else if (mode === 'before_after') {
                logicHint = 'Think about the order!';
            } else if (mode === 'number_pattern_hard' || mode === 'sequence_hard') {
                logicHint = 'Look for the rule \u2014 how does each number change?';
            } else if (mode === 'analogy_hard' || mode === 'word_analogy') {
                logicHint = 'Think about the relationship between the first pair!';
            } else if (mode === 'logic_deduction') {
                logicHint = 'Read the facts carefully \u2014 what MUST be true?';
            } else if (mode === 'matrix_pattern') {
                logicHint = 'Look at each row and column \u2014 what\u2019s the pattern?';
            } else if (mode === 'odd_one_out_hard') {
                logicHint = 'What category do three of them share?';
            }
            if (tPinyin) tPinyin.textContent = logicHint;
            if (tMeaning) tMeaning.textContent = '';

        } else if (gameType === 'english') {
            /* English hints */
            if (tChar) tChar.textContent = '\uD83D\uDCD6';
            var engHint = 'Try again!';
            if (mode === 'letter_sound') {
                engHint = 'Say the letter out loud!';
            } else if (mode === 'beginning_sound') {
                engHint = 'Say the word slowly \u2014 what\u2019s the first sound?';
            } else if (mode === 'rhyme_match') {
                engHint = 'Rhyming words sound the same at the end!';
            } else if (mode === 'cvc_blend') {
                engHint = 'Say each sound, then blend them together fast!';
            } else if (mode === 'sight_word_spell') {
                engHint = 'Look carefully at each letter!';
            } else if (mode === 'vocabulary_match') {
                engHint = 'Think about what this word means in a sentence!';
            } else if (mode === 'antonym_match') {
                engHint = 'Opposites! Think of the reverse!';
            } else if (mode === 'prefix_suffix' || mode === 'prefix_suffix_hard') {
                engHint = 'What does the prefix or suffix mean?';
            } else if (mode === 'vocabulary_hard') {
                engHint = 'Think about where you\u2019ve heard this word before!';
            } else if (mode === 'context_clues') {
                engHint = 'Read the sentence \u2014 which word makes sense?';
            } else if (mode === 'homophone_pick') {
                engHint = 'These words sound the same but are spelled differently!';
            } else if (mode === 'synonym_match') {
                engHint = 'Which word means the SAME thing?';
            } else if (mode === 'sentence_complete') {
                engHint = 'Read the sentence out loud \u2014 which sounds right?';
            }
            if (tPinyin) tPinyin.textContent = engHint;
            if (tMeaning) tMeaning.textContent = '';

        } else {
            /* Chinese hints — mode-specific clues without revealing the character */
            if (mode === 'char_to_image') {
                /* They see the character, hint = TTS + pinyin */
                if (tChar) tChar.textContent = '\uD83D\uDD0A';
                if (tPinyin) tPinyin.textContent = q.pinyin;
                if (tMeaning) tMeaning.textContent = 'Listen and look at the pinyin!';
                root.SkoolTTS.speakChinese(q.character);

            } else if (mode === 'image_to_char') {
                /* They see an image, hint = show the meaning text */
                if (tChar) tChar.textContent = '\uD83D\uDCA1';
                if (tPinyin) tPinyin.textContent = 'This means: ' + q.meaning;
                if (tMeaning) tMeaning.textContent = '';

            } else if (mode === 'char_to_meaning') {
                /* They see the character, hint = TTS + pinyin */
                if (tChar) tChar.textContent = '\uD83D\uDD0A';
                if (tPinyin) tPinyin.textContent = q.pinyin;
                if (tMeaning) tMeaning.textContent = 'Listen carefully!';
                root.SkoolTTS.speakChinese(q.character);

            } else if (mode === 'meaning_to_char') {
                /* They see the meaning, hint = pinyin */
                if (tChar) tChar.textContent = '\uD83D\uDCA1';
                if (tPinyin) tPinyin.textContent = q.pinyin;
                if (tMeaning) tMeaning.textContent = '';

            } else if (mode === 'fill_in_blank') {
                /* Hint = play TTS of the full word */
                if (tChar) tChar.textContent = '\uD83D\uDD0A';
                if (tPinyin) tPinyin.textContent = 'Listen to the word!';
                if (tMeaning) tMeaning.textContent = '';
                root.SkoolTTS.speakChinese(q.character);

            } else if (mode === 'pinyin_to_char') {
                /* They see pinyin, hint = meaning */
                if (tChar) tChar.textContent = '\uD83D\uDCA1';
                if (tPinyin) tPinyin.textContent = 'This means: ' + q.meaning;
                if (tMeaning) tMeaning.textContent = '';

            } else if (mode === 'audio_to_char') {
                /* Hint = replay audio + show pinyin */
                if (tChar) tChar.textContent = '\uD83D\uDD0A';
                if (tPinyin) tPinyin.textContent = q.pinyin;
                if (tMeaning) tMeaning.textContent = 'Listen again!';
                root.SkoolTTS.speakChinese(q.character);

            } else {
                /* Fallback: show pinyin as hint */
                if (tChar) tChar.textContent = '\uD83D\uDCA1';
                if (tPinyin) tPinyin.textContent = q.pinyin;
                if (tMeaning) tMeaning.textContent = '';
            }
        }

        /* Show panel */
        panel.classList.add('active');

        /* "Try again!" button → re-render question for retry */
        function onGotIt(e) {
            e.preventDefault();
            panel.classList.remove('active');
            tBtn.removeEventListener('click', onGotIt);
            tBtn.removeEventListener('touchend', onGotIt);

            /* Restore hidden elements for next time */
            if (tImage) tImage.style.display = '';
            if (tArrow) tArrow.style.display = '';

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

    /* ──────────────────────────────────────────────
       Bonus text overlay (Lucky Star, Speed Bonus)
       ────────────────────────────────────────────── */

    function showBonusText(text) {
        var el = document.createElement('div');
        el.style.cssText = 'position:fixed;top:30%;left:50%;transform:translate(-50%,-50%);' +
            'font-size:clamp(32px,7vw,56px);font-weight:900;color:#fdcb6e;z-index:300;' +
            'text-shadow:2px 4px 8px rgba(0,0,0,0.4);pointer-events:none;white-space:nowrap;';
        el.textContent = text;
        document.body.appendChild(el);
        el.animate([
            { transform: 'translate(-50%,-50%) scale(0.5)', opacity: 0 },
            { transform: 'translate(-50%,-50%) scale(1.3)', opacity: 1, offset: 0.3 },
            { transform: 'translate(-50%,-80%) scale(1)', opacity: 0 }
        ], { duration: 1500, easing: 'ease-out', fill: 'forwards' });
        setTimeout(function() { el.remove(); }, 1600);
    }


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

        /* Speak congratulation (Chinese TTS only for Chinese game) */
        if (gameType === 'chinese') {
            root.SkoolTTS.speakChinese('\u592A\u68D2\u4E86');    /* "tai bang le!" */
        }

        /* Call complete API, then redirect */
        root.SkoolAPI.completeSession(sessionId)
            .then(function () {
                setTimeout(function () {
                    root.location.href = '/game/session-complete/' + sessionId;
                }, 2200);
            })
            .catch(function (err) {
                console.error('[RacingGame] Complete error:', err);
                root.SkoolAPI.showError('Could not save results. Don\'t worry, try again!');
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

        /* Auto-speak the first character (handles iOS gesture requirement, Chinese only) */
        if (gameType === 'chinese') {
            root.SkoolTTS.autoSpeak(questions[0].character);
        }
    }

    /* Wait for DOM */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})(window);
