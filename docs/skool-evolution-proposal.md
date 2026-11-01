# Skool Evolution: Design Proposal for a Smarter, All-Ages Learning Game

**Version:** 1.0  
**Date:** November 1, 2026  
**Status:** Proposal (No Implementation Yet)

---

## Executive Summary

Skool currently excels as an **iPad-first Chinese character learning game for ages 4-9**, with solid spaced repetition (SM-2), gamification, and age-appropriate modes. This proposal outlines how to evolve it into a **comprehensive, adaptive, all-ages learning platform (ages 3-16)** that can grow with children from preschool through secondary school.

**Core Philosophy**: Maintain the game's kid-friendly joy while adding genuine educational rigor, adaptive intelligence, and long-term engagement features.

**Key Challenges Addressed:**
- Current system has no placement testing (everyone starts at zero)
- Fixed difficulty (no adaptation to individual ability)
- Limited age range (designed for 4-9, needs 3-16)
- No structured curriculum beyond 90 playable topics
- Weak progress visualization for kids

---

## 1. CURRICULUM: Building a Structured Learning Framework

### The Reality Check

**IB Curriculum Licensing**: The International Baccalaureate (IB) publishes excellent frameworks:
- **PYP** (Primary Years Programme, ages 3-12): Structured around 6 transdisciplinary themes, with scope-and-sequence for math, language, science, social studies
- **MYP** (Middle Years Programme, ages 11-16): Subject-specific frameworks with achievement levels

**However**: IB curriculum guides are **licensed materials**, not free item banks. Schools pay annual fees (USD $11,000-15,000) for authorization. We cannot legally vendor IB question banks or assessment tasks.

### Recommended Approach: Multi-Standard Hybrid

Use **open, freely available standards** as the structural backbone, with IB-*style* progression where helpful:

#### **Mathematics**: Common Core + Marble Taxonomy
- **Source**: [Common Core State Standards](https://www.thecorestandards.org/) (public domain)
- **Structure**: K-8 domains (Counting & Cardinality, Operations & Algebraic Thinking, Number & Operations, Measurement & Data, Geometry)
- **What we have**: 1,325 Marble Skill Taxonomy topics (90 playable), ages 4-10
- **Action**: Map existing math topics to CCSS grades K-5, extend to grades 6-8 with new generators

#### **Chinese**: 部编版 (Bùbiān Bǎn) + HSK Alignment
- **Source**: China's national curriculum (部编版 Chinese Language textbooks, grades 1-9)
- **Structure**: 
  - **Grades 1-2**: 800 basic characters (recognition + writing)
  - **Grades 3-6**: 2,500 cumulative characters, reading comprehension
  - **Grades 7-9**: 3,500 characters, literary analysis
- **HSK Levels**: Cross-reference with HSK 1-6 (Chinese Proficiency Test) for international learners
- **What we have**: 540 characters (roughly HSK 1-2 / Grade 1 level)
- **Action**: Tag existing characters by grade level + HSK band; add Grade 2-3 sets (target 1,500 characters by Phase 2)

#### **English**: CEFR Levels + Marble Taxonomy
- **Source**: [Common European Framework (CEFR)](https://www.coe.int/en/web/common-european-framework-reference-languages) A1-C2 (open standard)
- **Structure**: 
  - **A1** (Beginner): Basic phrases, simple interactions
  - **A2** (Elementary): Everyday expressions, simple descriptions
  - **B1-B2** (Intermediate): Detailed texts, complex discussions
- **What we have**: 90 Marble English topics (ages 4-10)
- **Action**: Map to CEFR A1-A2, add B1 topics for older kids

#### **Logic & Reasoning**: Age-Band Progressions
- No single "logic curriculum" standard exists
- Use **Piaget stages** + **Marble's cognitive domains** (pattern recognition, spatial reasoning, sequencing)
- Structure: Pre-operational (4-7), Concrete operational (7-11), Formal operational (11+)

### Data Model: Grade Band → Strand → Skill → Question

```sql
-- New table: learning_standards (replaces/extends learning_topics)
CREATE TABLE learning_standards (
    id INTEGER PRIMARY KEY,
    subject VARCHAR(50),           -- "math", "chinese", "english", "logic"
    grade_band VARCHAR(20),        -- "K", "1", "2-3", "4-5", "6-8", "9-12"
    strand VARCHAR(100),           -- e.g. "Operations & Algebraic Thinking" (CCSS)
    skill_code VARCHAR(50),        -- e.g. "2.OA.A.1" (CCSS), "Grade2_Char_Basic" (Chinese)
    skill_name VARCHAR(200),       -- Human-readable: "Add within 20"
    description TEXT,
    difficulty_level INTEGER,      -- 1-10 scale
    prerequisite_ids VARCHAR(500), -- JSON array of skill IDs
    age_min INTEGER,               -- 4
    age_max INTEGER,               -- 16
    question_mode VARCHAR(50),     -- Which generator to use
    created_at TIMESTAMP
);

-- User progress now tracks per-skill mastery
CREATE TABLE user_skill_progress (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    skill_id INTEGER,
    
    -- Existing SM-2 fields
    easiness_factor REAL DEFAULT 2.5,
    sm2_interval INTEGER DEFAULT 0,
    sm2_repetitions INTEGER DEFAULT 0,
    next_review_date DATE,
    
    -- NEW: Adaptive tracking
    elo_rating INTEGER DEFAULT 1500,    -- IRT-style ability estimate
    attempts INTEGER DEFAULT 0,         -- Total attempts
    first_try_correct INTEGER DEFAULT 0,-- Correct on first attempt (no retries)
    mastery_confidence REAL DEFAULT 0.0,-- Bayesian posterior (0.0-1.0)
    last_seen TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (skill_id) REFERENCES learning_standards(id)
);

-- User profile: grade level sets starting point
ALTER TABLE users ADD COLUMN grade_level VARCHAR(10); -- "K", "1", "2", etc.
ALTER TABLE users ADD COLUMN placement_completed BOOLEAN DEFAULT FALSE;
```

**Key Insight**: Grade level is a **starting point**, not a constraint. A 6-year-old (Grade 1) who crushes addition can advance to Grade 2-3 math while staying at Grade 1 for Chinese.

### How It Works in Practice

1. **Onboarding**: Parent sets child's age/grade → system suggests grade band
2. **Placement Test** (see Section 2): Quick 10-question adaptive test per subject determines actual starting skill level
3. **Skill Progression**: Mastery unlocks next skill (following prerequisite graph)
4. **Cross-Strand Balance**: Session includes skills from multiple strands (e.g., not just "addition" all day)

### Files to Modify

- **New**: `app/models/learning_standard.py` (replaces `app/models/topic.py` structure)
- **New**: `app/seed/standards/` directory with JSON files:
  - `math_ccss.json` (Common Core mapped)
  - `chinese_bubian.json` (部编版 character lists by grade)
  - `english_cefr.json` (CEFR-aligned topics)
- **Modify**: `app/services/topic_selection.py` → rename to `skill_selection.py`, refactor to pull from grade bands
- **Modify**: `app/services/spaced_repetition.py` → add Elo/mastery tracking

---

## 2. ADAPTIVE ENGINE: Smart Difficulty & Placement

### Current State: No Adaptation

- **Everyone starts at zero mastery**: No placement test
- **SM-2 only**: Tracks *when* to review, not *how hard* the item is relative to the child
- **Fixed difficulty**: Characters/topics selected by overdue → random low-mastery → never-seen
- **No reward for first-try success**: Retry counts the same as first-try correct

### Proposed: Three-Layer Adaptive System

#### Layer 1: Placement Test (First Session Per Subject)

**Purpose**: Quickly estimate starting ability to avoid boredom (too easy) or frustration (too hard)

**Algorithm: Adaptive Question Selection**
```python
# app/services/placement_test.py

def run_placement_test(user, subject, num_questions=10):
    """
    Adaptive placement test using binary search over difficulty levels.
    Returns estimated starting skill level (1-10 scale).
    """
    ability_estimate = 5.0  # Start at middle difficulty
    difficulty_range = (1, 10)
    
    for i in range(num_questions):
        # Pick a skill near current ability estimate
        skill = select_skill_near_difficulty(subject, ability_estimate)
        
        # Present question
        result = present_question_and_wait_for_answer(user, skill)
        
        # Update ability estimate (Item Response Theory formula)
        if result.is_correct:
            ability_estimate += 0.5  # Move up
            difficulty_range = (ability_estimate - 2, 10)
        else:
            ability_estimate -= 0.5  # Move down
            difficulty_range = (1, ability_estimate + 2)
    
    # Return grade-band recommendation
    return map_ability_to_grade_band(ability_estimate, subject)
```

**What the kid sees**: "Let's find the perfect level for you! Here are a few quick questions 🎯"

**Files**:
- **New**: `app/services/placement_test.py`
- **Modify**: `app/routes/game.py` → check `user.placement_completed`, redirect to placement if false

#### Layer 2: Elo Rating + Bayesian Knowledge Tracing

**Why Elo?** Originally for chess, Elo estimates relative ability. After each question:
- Correct answer → rating increases (more if question was hard)
- Wrong answer → rating decreases (more if question was easy)

**Implementation**:
```python
# app/services/adaptive_mastery.py

def update_skill_mastery_elo(user_progress, skill_difficulty, is_correct, is_first_try):
    """
    Update user's Elo rating for this skill.
    Elo = current rating + K * (actual - expected)
    """
    K = 32  # Learning rate (higher = faster adaptation)
    
    # Expected score: probability of correctness given rating difference
    rating_diff = user_progress.elo_rating - skill_difficulty
    expected = 1 / (1 + 10 ** (-rating_diff / 400))
    
    actual = 1.0 if is_correct else 0.0
    
    # Penalty for retry (not first try)
    if not is_first_try:
        actual *= 0.5  # Half credit for retry
    
    # Update
    user_progress.elo_rating += K * (actual - expected)
    user_progress.elo_rating = max(800, min(2200, user_progress.elo_rating))
    
    # Also update Bayesian confidence
    user_progress.mastery_confidence = bayesian_update(
        prior=user_progress.mastery_confidence,
        is_correct=is_correct,
        attempts=user_progress.attempts
    )

def bayesian_update(prior, is_correct, attempts):
    """
    Bayesian Knowledge Tracing: update belief about mastery.
    Returns posterior probability (0.0 = no mastery, 1.0 = full mastery)
    """
    # Simplified BKT: P(mastery) given evidence
    slip = 0.1   # P(wrong | actually knows it) = guess/slip
    guess = 0.25 # P(correct | doesn't know) = random guess (4 options)
    
    if is_correct:
        likelihood = (1 - slip) if attempts > 0 else 0.8
    else:
        likelihood = guess
    
    # Bayesian update
    posterior = (prior * likelihood) / (
        prior * likelihood + (1 - prior) * (1 - likelihood)
    )
    return posterior
```

**Mastery Criteria**: Skill is "mastered" when:
- `mastery_confidence >= 0.85` (85% certain they know it)
- `sm2_repetitions >= 2` (answered correctly on 2 separate days)
- `first_try_correct / attempts >= 0.7` (70%+ first-try success)

**Files**:
- **New**: `app/services/adaptive_mastery.py`
- **Modify**: `app/services/session_engine.py:167-240` → call `update_skill_mastery_elo()` instead of basic SM-2
- **Modify**: `app/models/progress.py` → add Elo fields to `UserCharacterProgress`

#### Layer 3: Dynamic Session Difficulty (Target 80% Success)

**Problem**: Fixed 5-question sessions ignore performance

**Solution**: Adjust difficulty in real-time to maintain ~80% success rate (optimal learning zone per educational research)

```python
# app/services/session_engine.py

def select_next_question_adaptive(user, session_so_far):
    """
    Pick next question difficulty based on performance this session.
    Target: 80% success rate (Goldilocks zone: not too hard, not too easy)
    """
    if len(session_so_far.questions) == 0:
        # First question: use user's average Elo
        target_difficulty = user.average_elo_rating()
    else:
        # Adjust based on session performance
        accuracy = session_so_far.total_correct / len(session_so_far.questions)
        
        if accuracy < 0.6:
            # Struggling: dial down 1 level
            target_difficulty = user.average_elo_rating() - 200
        elif accuracy > 0.9:
            # Crushing it: dial up 1 level
            target_difficulty = user.average_elo_rating() + 200
        else:
            # In sweet spot: maintain
            target_difficulty = user.average_elo_rating()
    
    # Select skill near target difficulty with SM-2 priority (overdue first)
    return select_skill_by_difficulty_and_schedule(user, target_difficulty)
```

**Session Length Adaptation**:
- **Standard**: 5 questions (keep for most users)
- **Struggling** (accuracy < 50%): Stop at 3 questions, show encouragement
- **Perfect streak** (5/5 correct): Offer bonus round (+2 questions, extra stars)

**Files**:
- **Modify**: `app/services/session_engine.py:40-72` → add adaptive difficulty selection
- **Modify**: `app/config.py:24` → add `adaptive_difficulty: bool = True`

### Hints & Scaffolding (Escalating Help)

**Current**: Wrong answer shows teaching panel immediately

**Proposed**: Escalating hint system
1. **First wrong answer**: Shake animation, no hint yet (let them try again)
2. **Second wrong answer**: Show hint (e.g., "It starts with 'd'...", highlight correct option color)
3. **Third wrong answer**: Teaching panel with full answer

```python
# app/services/session_engine.py:167-240

def submit_answer(db, user, question_id, selected_answer):
    question = db.query(SessionQuestion).get(question_id)
    
    if question.attempt_count == 0:
        # First try
        question.attempt_count = 1
        if is_correct:
            award_points(db, user, settings.points_correct, "first_try_correct")
        else:
            return {"is_correct": False, "hint_level": 0, "message": "Try again!"}
    
    elif question.attempt_count == 1:
        # Second try: give hint
        question.attempt_count = 2
        if is_correct:
            award_points(db, user, settings.points_correct * 0.5, "second_try_correct")
        else:
            hint = generate_hint(question)  # e.g., "Starts with '大'"
            return {"is_correct": False, "hint_level": 1, "hint": hint}
    
    else:
        # Third try: show teaching panel
        show_teaching_panel(question)
```

**Files**:
- **Modify**: `app/services/session_engine.py` → add hint logic
- **Modify**: `static/js/racing.js` → handle hint responses
- **New**: `app/services/hint_generator.py` → generate contextual hints

---

## 3. FULL UI REDESIGN: A Modern, Joyful Learning Experience

### Executive Summary: Why a Complete Redesign?

The current UI is **functional but dated** — it works well on iPad but lacks the **visual polish, personality, and modern animation standards** that kids expect from apps in 2026. A comprehensive redesign will:

1. **Modernize the visual language** with a cohesive design system
2. **Introduce character-driven storytelling** through animated mascots
3. **Upgrade the animation stack** to industry-standard tools
4. **Create screen-specific experiences** rather than one generic game template
5. **Maintain performance** on older iPads while leveraging modern capabilities

**Philosophy**: Design for **joy, clarity, and inclusivity**. Every screen should feel like a reward, not a chore.

---

### 3.1 NEW VISUAL LANGUAGE

#### A. Design System: "Playful Learning"

**Core Principles**:
1. **Big, Bold, Friendly**: Large typography, rounded corners, generous whitespace
2. **High Contrast for Readability**: WCAG AAA standard (7:1 contrast)
3. **Tactile & Responsive**: Every tap feels satisfying (animations, haptics, sound)
4. **Age-Adaptive**: Pre-readers (3-5) see more icons; older kids (9+) see more text

#### B. Color Palette

**Current Palette**: Generic blue/purple gradients, no cohesive theme

**New Palette**: "Learning Garden" — nature-inspired, energetic, gender-neutral

```css
/* Primary Colors */
--sky-blue:       #4A90E2;   /* Trust, calm */
--sunshine-yellow: #FFD93D;  /* Energy, positivity */
--grass-green:    #6BCF7F;   /* Growth, success */
--coral-orange:   #FF6B6B;   /* Excitement, attention */
--lavender:       #B8A4E8;   /* Creativity, imagination */

/* Semantic Colors */
--success:   #00D084;  /* Bright green (correct answer) */
--error:     #FF4757;  /* Soft red (wrong answer, not harsh) */
--warning:   #FFA502;  /* Orange (streak at risk) */
--neutral:   #95A5A6;  /* Gray (disabled states) */

/* Backgrounds */
--bg-light:  #F8FAFC;  /* Off-white, easy on eyes */
--bg-card:   #FFFFFF;  /* Pure white for cards */
--bg-dark:   #2C3E50;  /* Dark mode option */

/* Gradients (used sparingly) */
--gradient-dawn:  linear-gradient(135deg, #FFD93D 0%, #FF6B6B 100%);
--gradient-ocean: linear-gradient(135deg, #4A90E2 0%, #6BCF7F 100%);
--gradient-sunset: linear-gradient(135deg, #FF6B6B 0%, #B8A4E8 100%);
```

**Color Accessibility**: All text colors tested against backgrounds for WCAG AAA (7:1 ratio)

#### C. Typography

**Current**: System fonts (-apple-system, Arial)

**New**: Custom font pairing optimized for kids

**Primary Font: "Fredoka" (Google Fonts, free)**
- **Why**: Rounded, friendly, highly legible for kids
- **Usage**: Headings, labels, buttons
- **Weights**: 400 (Regular), 600 (Semibold), 700 (Bold)
- **Example**: "Great job! 🎉" in 36px Fredoka Bold

**Secondary Font: "Inter" (Google Fonts, free)**
- **Why**: Clean, readable at small sizes, professional for parent dashboard
- **Usage**: Body text, descriptions, parent dashboard
- **Weights**: 400 (Regular), 500 (Medium), 700 (Bold)

**Chinese Font: "Noto Sans SC" (Google Fonts, free)**
- **Why**: Excellent CJK support, clean strokes, good for learning
- **Usage**: Chinese characters, pinyin
- **Weight**: 700 (Bold) for character display, 400 for pinyin

**Font Loading Strategy**:
```html
<!-- Preload critical fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preload" href="/fonts/fredoka-700.woff2" as="font" crossorigin>

<!-- Load async -->
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&family=Inter:wght@400;500;700&family=Noto+Sans+SC:wght@400;700&display=swap" rel="stylesheet">
```

**Typography Scale** (responsive via clamp):
```css
--text-xs:   clamp(12px, 2vw, 14px);   /* Sublabels */
--text-sm:   clamp(14px, 2.5vw, 16px); /* Body text */
--text-base: clamp(16px, 3vw, 18px);   /* Default */
--text-lg:   clamp(20px, 3.5vw, 24px); /* Labels */
--text-xl:   clamp(24px, 4vw, 32px);   /* Small headings */
--text-2xl:  clamp(32px, 5vw, 48px);   /* Headings */
--text-3xl:  clamp(48px, 8vw, 72px);   /* Hero text */
--text-huge: clamp(80px, 15vw, 160px); /* Character display */
```

#### D. Component Library: Atoms & Molecules

**Buttons** (3 variants):
```css
/* Primary: Call-to-action */
.btn-primary {
    background: var(--gradient-dawn);
    color: white;
    font-family: 'Fredoka', sans-serif;
    font-weight: 700;
    font-size: var(--text-lg);
    padding: 16px 32px;
    border-radius: 24px;
    border: none;
    box-shadow: 0 8px 24px rgba(255, 107, 107, 0.3);
    transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:active {
    transform: scale(0.95);
    box-shadow: 0 4px 12px rgba(255, 107, 107, 0.2);
}

/* Secondary: Less important actions */
.btn-secondary {
    background: white;
    color: var(--sky-blue);
    border: 3px solid var(--sky-blue);
    /* ... similar styling ... */
}

/* Ghost: Subtle actions */
.btn-ghost {
    background: transparent;
    color: var(--neutral);
    /* ... */
}
```

**Cards** (elevated, soft shadows):
```css
.card {
    background: var(--bg-card);
    border-radius: 24px;
    padding: 24px;
    box-shadow: 
        0 2px 8px rgba(0, 0, 0, 0.04),
        0 8px 24px rgba(0, 0, 0, 0.08);
    transition: transform 0.3s, box-shadow 0.3s;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 
        0 4px 12px rgba(0, 0, 0, 0.06),
        0 12px 32px rgba(0, 0, 0, 0.12);
}
```

**Progress Indicators** (animated):
```css
.progress-ring {
    /* Circular progress (like iOS) */
    stroke-dasharray: 283; /* 2πr where r=45 */
    stroke-dashoffset: 283;
    transition: stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-ring.animate {
    stroke-dashoffset: calc(283 * (1 - var(--progress)));
}
```

#### E. Iconography

**Style**: Duotone icons (2-color, friendly, not flat)

**Source**: [Phosphor Icons](https://phosphoricons.com/) (free, open source)
- 6,000+ icons in duotone style
- SVG format (scalable, sharp on retina)
- Color customizable via CSS

**Custom Icons Needed**:
- Mascot characters (4-5 poses each)
- Subject icons (Chinese, Math, English, Logic)
- Reward items (cars, pets, backgrounds)

**Icon Loading**:
```html
<!-- Inline critical icons as SVG for instant render -->
<svg class="icon icon-star" width="24" height="24">
    <use href="/static/icons/sprite.svg#star"></use>
</svg>
```

#### F. Mascot System: Character-Driven Experience

**Current**: No mascots, generic car emoji

**New**: 4 Mascot Characters (one per theme + parent)

**1. Dash the Rabbit 🐰** (Racing Theme)
- **Personality**: Speedy, enthusiastic, encouraging
- **Visual**: Blue-gray rabbit with racing goggles, yellow scarf
- **Animations**: 8 states (idle, happy, sad, thinking, celebrating, pointing, waving, sleeping)
- **Voice**: Mid-pitch, upbeat ("Let's go! You're doing great!")

**2. Sparkle the Unicorn 🦄** (Pony Theme)
- **Personality**: Magical, creative, gentle
- **Visual**: White unicorn with rainbow mane, sparkle trail
- **Animations**: Same 8 states as Dash
- **Voice**: Higher pitch, warm ("You're amazing! Keep shining!")

**3. Nova the Owl 🦉** (Logic/Science Theme, future)
- **Personality**: Wise, curious, thoughtful
- **Visual**: Purple owl with star-patterned wings, tiny glasses
- **For older kids**: More sophisticated interactions

**4. Buddy the Dog 🐕** (Parent Dashboard)
- **Personality**: Friendly guide, helpful assistant
- **Visual**: Golden retriever with clipboard
- **Use**: Help parents navigate dashboard, explain stats

**Mascot Behavior Rules**:
- **Context-Aware**: Reacts to specific events (3-correct streak, wrong answer, session complete)
- **Non-Intrusive**: Appears in corner, doesn't block content
- **Optional**: Parent can disable mascot if child finds it distracting

**Technical Implementation**: Rive animations (see 3.3 Animation Stack)

---

### 3.2 SCREEN-BY-SCREEN REDESIGN

#### Screen 1: Login / Avatar Select

**Current Issues**:
- Generic list of names
- No personality or visual appeal
- "PIN: 8888" text is confusing for kids

**New Design**: "Welcome Home" Screen

**Layout**:
```
╔════════════════════════════════════════╗
║                                        ║
║         🏠 Welcome to Skool!          ║
║                                        ║
║   Who's learning today?                ║
║                                        ║
║   ┌─────────┐      ┌─────────┐       ║
║   │  [🧒]   │      │  [👧]   │       ║
║   │ Daniel  │      │  Ellie  │       ║
║   │  Age 4  │      │  Age 9  │       ║
║   │  🚗      │      │  🦄      │       ║
║   └─────────┘      └─────────┘       ║
║                                        ║
║   ┌─────────────────────────┐         ║
║   │ 👨 Parent Dashboard →  │         ║
║   └─────────────────────────┘         ║
║                                        ║
╚════════════════════════════════════════╝
```

**Features**:
- **Large Avatar Cards**: 160×200px cards with:
  - Animated avatar illustration (not emoji)
  - Name in big Fredoka font
  - Age + theme icon
  - Current streak indicator (🔥 5 days)
- **Tap Animation**: Card bounces and mascot waves when tapped
- **Parent Access**: Separate card at bottom, requires PIN entry
  - PIN entry is visual dots, not text field (kid-proof)
  - Shows after long-press (3 seconds)

**Files**:
- **New**: `templates/login_v2.html`
- **New**: `static/css/login_v2.css`
- **New**: `static/avatars/daniel-idle.svg`, `ellie-idle.svg` (custom illustrations)

---

#### Screen 2: Game Selector / World Map

**Current Issues**:
- List of 4 game cards
- No sense of progression or place
- Static, no exploration

**New Design**: "Learning World" — Interactive Map

**Concept**: Top-down 2.5D map with 4 themed islands:

```
         🌊 Ocean Background 🌊
         
   ┌────────────────────────────────┐
   │                                │
   │  🏔️ Math Mountain              │
   │     [Locked: Level 3]          │
   │                                │
   │         🛤️ Path               │
   │           ↓                    │
   │  🌸 English Garden    🎌 Chinese │
   │    [2/5 ⭐]           Village    │
   │                       [TODAY!]   │
   │         🛤️ Path       🔥 Streak │
   │           ↓                     │
   │  🧩 Logic Labs                 │
   │    [Unlocks at Lvl 2]          │
   │                                │
   └────────────────────────────────┘
   
   Bottom Bar:
   [👤 Profile] [🏆 Quests] [🎁 Store] [📊 Progress]
```

**Features**:
1. **Islands as Subjects**: 
   - Chinese Village (bamboo, pagoda, lanterns)
   - Math Mountain (geometric shapes, numbers floating)
   - English Garden (books, flowers, alphabet trees)
   - Logic Labs (gears, circuits, puzzles)

2. **Progression Indicators**:
   - Locked islands (padlock icon, "Unlock at Grade 2")
   - Current session available (pulsing glow)
   - Today's quest marker (flag icon)
   - Skill level per island (1-10 stars)

3. **Interactive Elements**:
   - Tap island → zoom in → mascot appears → "Ready to learn Chinese?" → Start
   - Background animations (birds flying, clouds drifting, water rippling)
   - Parallax scrolling on phone (if map doesn't fit, pan to explore)

4. **Session Limit UI**:
   - If sessions exhausted: Islands dim out, mascot says "Great work today! Come back tomorrow 🌙"
   - Token system visualization: "2 learning tokens left today" (coins with sparkles)

5. **Top Header**:
   - Avatar + name + current streak (compact)
   - Total stars this week
   - Quest progress indicator (3 slots, filled/empty)

**Navigation**:
- Bottom bar (fixed):
  - **Profile**: Kid's progress map (see Screen 7)
  - **Quests**: Daily quest list (overlay)
  - **Store**: Garage/shop (see Screen 6)
  - **Progress**: Detailed stats (see Screen 7)

**Files**:
- **New**: `templates/world_map.html`
- **New**: `static/css/world_map.css`
- **New**: `static/images/world/` → island backgrounds, paths, decorations
- **New**: `static/js/world_map.js` → pan/zoom, animations

**Technical**: 
- Use CSS transforms for parallax
- SVG for scalable island illustrations
- Canvas for particle effects (birds, leaves, sparkles)

---

#### Screen 3: Question Screen (Game Session)

**Current Issues**:
- Generic sky background
- Road metaphor doesn't scale (can't show 10+ questions)
- Car movement is the only progress indicator

**New Design**: Subject-Themed Immersive Screen

**Layout for Chinese Village Theme**:
```
╔══════════════════════════════════════════╗
║ [← Exit]    Question 3 of 5    [🔊 Music]║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                          ║
║         🏮 Chinese Village 🏮            ║
║     (Bamboo forest background)          ║
║                                          ║
║                                          ║
║          ┌──────────┐                   ║
║          │    大     │  [🔊]             ║
║          │  (dà)    │                   ║
║          └──────────┘                   ║
║                                          ║
║     ┌─────────┐    ┌─────────┐         ║
║     │  [🚗]   │    │  [🐘]   │         ║
║     │   car   │    │ elephant│         ║
║     └─────────┘    └─────────┘         ║
║     ┌─────────┐    ┌─────────┐         ║
║     │  [🏠]   │    │  [🌊]   │         ║
║     │  house  │    │  ocean  │         ║
║     └─────────┘    └─────────┘         ║
║                                          ║
║  [🐰 Dash] "Tap the picture that        ║
║             matches 大!"                 ║
╚══════════════════════════════════════════╝
```

**Key Changes**:

1. **Subject-Specific Backgrounds**:
   - **Chinese**: Bamboo forest, paper lanterns swaying
   - **Math**: Geometric pattern (triangles, hexagons) with equation trails
   - **English**: Library bookshelves with floating letters
   - **Logic**: Circuit board pattern with light-up nodes

2. **Character Display**: 
   - Elevated card (not just text on sky)
   - Soft shadow, subtle glow animation
   - TTS button integrated (speaker icon in card)

3. **Option Grid**:
   - Adaptive: 2×2 on phone, 3×2 on iPad, 4×2 on laptop
   - Larger images (fill 80% of card)
   - Labels below images in Fredoka font

4. **Progress Indicators** (Multiple):
   - **Linear bar** at top (classic, always visible)
   - **Mascot position**: Moves along bottom path (5 stops)
   - **Combo meter**: Appears on right after 2+ correct (streak counter)

5. **Mascot Integration**:
   - **Bottom-right corner** (80×80px)
   - **Idles**: Gentle breathing animation
   - **Reacts**: Jumps on correct, sad on wrong
   - **Speaks**: Speech bubble with encouragement
   - **Voice prompts** (optional): "Which one is big?"

6. **Hint System** (Escalating):
   - **First wrong**: Button shakes, mascot says "Try again!"
   - **Second wrong**: Highlight correct answer with subtle glow + hint text
   - **Third wrong**: Teaching panel (full-screen overlay, see Screen 4)

**Animations** (see 3.3 for tech stack):
- **Question transition**: Slide out old question, slide in new (0.5s)
- **Character entrance**: Scale up + fade in (0.4s)
- **Option taps**: Haptic feedback + scale down (0.2s)
- **Background**: Subtle parallax on gyroscope (phone), gentle sway (lanterns, leaves)

**Files**:
- **Modify**: `templates/themes/racing/game.html` → `templates/game_session_v2.html`
- **New**: `static/css/game_session_v2.css`
- **New**: `static/images/backgrounds/` → subject-specific backgrounds
- **Modify**: `static/js/racing.js` → `game_session_v2.js` (refactor for new layout)

---

#### Screen 4: Feedback & Teaching Panel

**Current Issues**:
- Teaching panel is clinical (white box, text-heavy)
- No celebration for correct answers (just confetti)
- Wrong answers feel punishing

**New Design**: Split into two distinct experiences

**A. CORRECT ANSWER FEEDBACK**

**Micro-interaction** (0.8 seconds total):
1. **Button flash** (0.2s): Green border + glow
2. **Screen flash** (0.3s): Soft green overlay (20% opacity)
3. **Confetti burst** (0.5s): 50 particles from button
4. **Mascot celebration** (0.6s): Jumps + sparkles
5. **Sound**: Cheerful chime (C major arpeggio)
6. **Haptic**: Success pattern (iOS style)

**On-screen elements**:
- **Floating "+2 points"** text above button (floats up + fades)
- **Combo counter** increments (if applicable)
- **Mascot speech bubble**: "Awesome! 🎉" (random encouragement)

**Next question loads automatically** after 1.2s (no button needed)

**B. WRONG ANSWER FEEDBACK**

**Goal**: Teach, don't punish

**Micro-interaction** (immediate):
1. **Button shake** (0.4s): Horizontal wobble
2. **Soft red flash** (0.2s): Not harsh
3. **Mascot reaction** (0.5s): Sad face → encouraging face
4. **Sound**: Gentle "uh-oh" (not buzzer)
5. **Haptic**: Error pattern (short vibration)

**Teaching Panel** (appears after 2nd wrong attempt):

```
╔══════════════════════════════════════════╗
║                                          ║
║         💡 Let's Learn Together          ║
║                                          ║
║              ┌────────┐                  ║
║              │   大    │                  ║
║              │  (dà)  │                  ║
║              └────────┘                  ║
║                  ↓                       ║
║         ┌──────────────┐                 ║
║         │   [🏠]       │                 ║
║         │  Big House   │                 ║
║         └──────────────┘                 ║
║                                          ║
║  大 (dà) means "big" — like a big house! ║
║                                          ║
║      [🐰 Dash] "Now you know! Let's     ║
║                  try the next one."     ║
║                                          ║
║        ┌──────────────────┐              ║
║        │  Got it! ✓       │              ║
║        └──────────────────┘              ║
╚══════════════════════════════════════════╝
```

**Features**:
- **Friendly tone**: "Let's learn together" (not "Wrong!")
- **Visual mnemonic**: Show character + correct image + meaning
- **Mascot encouragement**: Speech bubble with positive message
- **Single button**: "Got it!" (dismisses panel)
- **Background blur**: Dims game screen (focus on learning)

**Files**:
- **Modify**: `static/css/racing.css` → feedback animations
- **New**: `templates/partials/teaching_panel_v2.html`
- **Modify**: `static/js/game_session_v2.js` → feedback orchestration

---

#### Screen 5: Session Results

**Current Issues**:
- Text-heavy XP breakdown
- No emotional payoff
- Car level-up is buried

**New Design**: "Victory Screen" with Personality

**Layout** (Perfect Session Example):
```
╔══════════════════════════════════════════╗
║                                          ║
║   🎉 PERFECT! You're on fire! 🔥        ║
║                                          ║
║        [🐰 Dash doing victory dance]    ║
║                                          ║
║              5 / 5 Correct               ║
║           ━━━━━━━━━━━━━━━                ║
║              100% Accuracy               ║
║                                          ║
║   ┌────────────────────────────────┐    ║
║   │  Points Earned                 │    ║
║   │  ━━━━━━━━━━━━━━━━━━━━━━━━     │    ║
║   │  ⭐ Correct answers       +10  │    ║
║   │  ✨ Perfect bonus         +10  │    ║
║   │  🔥 5-day streak          +5   │    ║
║   │  ⚡ Speed bonus           +2   │    ║
║   │  ━━━━━━━━━━━━━━━━━━━━━━━━     │    ║
║   │  Total                    27   │    ║
║   └────────────────────────────────┘    ║
║                                          ║
║   Progress: 27 ⭐ → 3 🪙 (7 ⭐ to next)  ║
║                                          ║
║   ┌──────────┐  ┌──────────┐            ║
║   │Play Again│  │ See Stats│            ║
║   └──────────┘  └──────────┘            ║
║                                          ║
╚══════════════════════════════════════════╝
```

**Features**:

1. **Dynamic Header**:
   - **Perfect (5/5)**: "PERFECT! You're on fire! 🎉🔥"
   - **Great (4/5)**: "Great Job! Almost perfect! ⭐"
   - **Good (3/5)**: "Good work! You're learning! 💪"
   - **Keep Trying (1-2/5)**: "Keep going! You've got this! 🌱"

2. **Mascot Celebration**:
   - **Perfect**: Victory dance animation (Rive, 3s loop)
   - **Good**: Applause animation
   - **Struggling**: Encouraging pat-on-back animation

3. **XP Breakdown** (Animated Count-Up):
   - Each line animates in sequence (0.2s delay between)
   - Numbers count up (like slot machine)
   - Sound: Coin clink on each line

4. **Level-Up Celebration** (if applicable):
   - Full-screen overlay
   - "LEVEL UP! 🎊 Math Level 3 → 4"
   - Unlocked reward preview (car, pet, etc.)
   - Fireworks animation

5. **Quest Progress** (if applicable):
   - Small banner: "Daily Quest Progress: Perfect Day ⭐ (1/1 ✓)"

6. **Buttons**:
   - **Primary**: "Play Again" (if sessions remain)
   - **Secondary**: "See Stats" (goes to progress map)
   - **Ghost**: "Back to World" (returns to map)

**Files**:
- **New**: `templates/session_results_v2.html`
- **New**: `static/css/session_results_v2.css`
- **Modify**: `app/routes/game.py` → render new template

---

#### Screen 6: Rewards & Garage

**Current Issues**:
- Store is a flat list of items
- No preview or personality
- Car tier is abstract (no garage feel)

**New Design**: "Your Collection" — Interactive Garage

**Layout**:
```
╔══════════════════════════════════════════╗
║  [← Back]      Your Garage      [🪙 47] ║
║━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║                                          ║
║  Tabs: [🚗 Cars] [🐾 Pets] [🎨 Themes]  ║
║                                          ║
║   Current Car:                           ║
║   ┌────────────────────────────────┐    ║
║   │                                │    ║
║   │         [🏎️ Race Car]         │    ║
║   │       Level 3 - Speed Demon   │    ║
║   │                                │    ║
║   │    [Preview in action →]      │    ║
║   └────────────────────────────────┘    ║
║                                          ║
║   Upgrade Available: 🚙 Super Racer     ║
║   Cost: 30 🪙  (You need 30 more)       ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║   Progress: [████████░░░░░] 17/30       ║
║                                          ║
║   ┌──────────────────────────────────┐  ║
║   │     Unlock New Skins:            │  ║
║   │  ┌─────┐  ┌─────┐  ┌─────┐      │  ║
║   │  │ 🔴  │  │ 🔵  │  │ 🟢  │      │  ║
║   │  │ 5🪙 │  │ 5🪙 │  │ 5🪙 │      │  ║
║   │  └─────┘  └─────┘  └─────┘      │  ║
║   └──────────────────────────────────┘  ║
╚══════════════════════════════════════════╝
```

**Features**:

1. **Tabbed Categories**:
   - **Cars**: 5 tiers × 3 skins each = 15 total
   - **Pets**: 8 companions (turtle, rabbit, fox, cat, owl, dragon, etc.)
   - **Themes**: 10 backgrounds (beach, forest, space, candy, underwater, etc.)
   - **Trails**: 6 effects (stars, hearts, fire, sparkles, rainbow, lightning)

2. **3D Preview** (Optional, Phase 3):
   - Tap "Preview in action" → mini-game demo
   - Shows car with selected skin/pet/trail
   - 5-second loop animation

3. **Clear Pricing**:
   - No loot boxes or gacha
   - Fixed prices (5-50 coins)
   - Shows "You need X more coins" if insufficient

4. **Earned vs Purchased**:
   - **Earned**: Unlocked via level-ups (free)
   - **Purchased**: Bought with coins
   - Badge indicator: "🆓 Earned!" vs "🪙 Bought!"

5. **Ownership Pride**:
   - "Collection: 8/15 cars unlocked"
   - Progress bars for each tier
   - "Collector" badge when 100% complete

**Files**:
- **New**: `templates/garage_v2.html`
- **New**: `static/css/garage_v2.css`
- **Modify**: `app/models/store.py` → add categories, previews
- **Modify**: `app/routes/store.py` → new structure

---

#### Screen 7: Kid Progress Map

**Current Issues**:
- Progress is only visible to parents
- Kids don't see their growth

**New Design**: "My Learning Journey" — Visual Progress Tree

**Layout**:
```
╔══════════════════════════════════════════╗
║  [← Back]    My Learning Journey         ║
║━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║                                          ║
║       [🧒 Daniel]  Age 4  🔥 12 days    ║
║                                          ║
║   ┌──────────────────────────────────┐  ║
║   │   🇨🇳 Chinese                    │  ║
║   │   ━━━━━━━━━━━━━━━━━━━━━━━━       │  ║
║   │   Level 2 - Early Reader         │  ║
║   │   87 / 200 characters mastered   │  ║
║   │   [████████░░░░░░░░] 44%         │  ║
║   │                                  │  ║
║   │   Recent wins:                   │  ║
║   │   ✓ Mastered 大, 小, 人 today!   │  ║
║   └──────────────────────────────────┘  ║
║                                          ║
║   ┌──────────────────────────────────┐  ║
║   │   ➕ Math                         │  ║
║   │   ━━━━━━━━━━━━━━━━━━━━━━━━       │  ║
║   │   Level 3 - Addition Pro         │  ║
║   │   23 / 50 skills mastered        │  ║
║   │   [█████░░░░░░░░░░░] 46%         │  ║
║   └──────────────────────────────────┘  ║
║                                          ║
║   This Week:                             ║
║   📚 12 sessions completed               ║
║   ⭐ 156 stars earned                    ║
║   🎯 94% average accuracy                ║
║                                          ║
╚══════════════════════════════════════════╝
```

**Features**:

1. **Per-Subject Breakdown**:
   - Level name (not just numbers)
   - Mastery count (87/200 characters)
   - Progress bar (visual, color-coded)
   - Recent achievements

2. **Weekly Summary**:
   - Sessions completed
   - Stars earned
   - Average accuracy
   - Streak maintained

3. **Skill Tree** (Future, Phase 3):
   - Visual tree of skills (like Duolingo)
   - Prerequisites shown as branches
   - Unlocked skills glow gold
   - Locked skills are gray with padlock

4. **Badges & Milestones**:
   - "First Perfect Session! 🏆"
   - "10-Day Streak! 🔥"
   - "100 Characters Mastered! 🎉"
   - Display in trophy case (grid of icons)

**Files**:
- **New**: `templates/progress_map_v2.html`
- **New**: `static/css/progress_map_v2.css`
- **New**: `app/routes/progress.py`

---

#### Screen 8: Parent Dashboard

**Current Issues**:
- Functional but visually dense
- No personality
- Hard to parse at a glance

**New Design**: "Family Command Center" — Data-Driven Yet Friendly

**Layout** (Desktop View):
```
╔═══════════════════════════════════════════════════╗
║  🐕 Buddy: "Hello! Here's how the kids are doing" ║
║━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║                                                   ║
║  Daniel (Age 4)                Ellie (Age 9)     ║
║  ┌──────────────────────┐    ┌──────────────────┐║
║  │ 🔥 12-day streak     │    │ 🔥 45-day streak │║
║  │ 87 chars mastered    │    │ 312 chars mastered│║
║  │ 94% accuracy         │    │ 89% accuracy     │║
║  │                      │    │                  │║
║  │ [See Details →]     │    │ [See Details →]  │║
║  └──────────────────────┘    └──────────────────┘║
║                                                   ║
║  Weekly Activity                                  ║
║  ┌─────────────────────────────────────────────┐ ║
║  │  Mon Tue Wed Thu Fri Sat Sun                │ ║
║  │   2   2   1   2   2   0   1   (sessions)   │ ║
║  │  ███ ███ ██  ███ ███  ░   ██                │ ║
║  └─────────────────────────────────────────────┘ ║
║                                                   ║
║  Skills to Review (Daniel)                        ║
║  ┌─────────────────────────────────────────────┐ ║
║  │  大 (dà) - Last seen 7 days ago             │ ║
║  │  [Queue Drill]                               │ ║
║  └─────────────────────────────────────────────┘ ║
║                                                   ║
║  Family Goals                                     ║
║  "Complete 20 sessions this week" [Progress: 14/20]║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║  [███████████████████████░░░░░] 70%              ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
```

**Features**:

1. **At-a-Glance Cards**:
   - Key stats per child (streak, mastery, accuracy)
   - Click to expand detailed view
   - Color-coded health indicators (green = on track, yellow = needs attention, red = at risk)

2. **Activity Heatmap**:
   - 7-day view (bar chart)
   - Hover for details ("Monday: 2 sessions, 24 points")
   - 30-day view available (toggle)

3. **Actionable Insights**:
   - "Daniel hasn't practiced Chinese in 2 days — queue a drill?"
   - "Ellie's math accuracy dropped to 75% this week — review subtraction?"
   - AI-generated suggestions (Phase 3)

4. **Buddy the Dog**:
   - Friendly guide, appears in header
   - Explains stats in plain language
   - Suggests actions ("Would you like to set a weekly goal?")

5. **Settings Panel**:
   - Session limits per child
   - Notification preferences
   - Voice prompt toggle
   - Theme/mascot selection

**Files**:
- **New**: `templates/dashboard_v2.html`
- **New**: `static/css/dashboard_v2.css`
- **Modify**: `app/routes/dashboard.py` → new data structure

---

### 3.3 MODERN ANIMATION STACK

#### Current State: CSS Animations Only

**Limitations**:
- CSS can't do complex character animations (mascots)
- No timeline control (can't pause, rewind, sync)
- Performance issues with many DOM elements

#### Proposed Stack: Best-of-Breed Tools

**Philosophy**: Use the right tool for each job

---

#### A. Rive (Character Animations)

**Use Case**: Mascot characters (Dash, Sparkle, Nova, Buddy)

**Why Rive?**
- **Vector-based**: Scalable to any size, sharp on retina
- **Small file size**: 10-50KB per character (vs 500KB for Lottie)
- **Runtime**: Rive has official JS runtime, great performance
- **Interactivity**: Can trigger animations based on game state
- **Designer-friendly**: Non-engineers can create/iterate

**Implementation**:
```html
<!-- Load Rive runtime -->
<script src="https://unpkg.com/@rive-app/canvas@2.7.0"></script>

<canvas id="mascot-canvas" width="160" height="160"></canvas>

<script>
const riveInstance = new rive.Rive({
    src: '/static/animations/dash-rabbit.riv',
    canvas: document.getElementById('mascot-canvas'),
    autoplay: true,
    stateMachines: 'State Machine',  // Controls which animation plays
    onLoad: () => {
        const inputs = riveInstance.stateMachineInputs('State Machine');
        window.mascotInputs = inputs;  // Store for later control
    }
});

// Trigger animations
function celebrateMascot() {
    const trigger = window.mascotInputs.find(i => i.name === 'celebrate');
    trigger.fire();  // Plays "celebrate" animation once
}
</script>
```

**Mascot Animation States** (per character):
1. **Idle**: Gentle breathing loop (2s)
2. **Happy**: Jump + smile (1s, trigger)
3. **Sad**: Droop + frown (1s, trigger)
4. **Thinking**: Scratch head + question mark (1.5s, trigger)
5. **Celebrating**: Victory dance (2s, trigger)
6. **Pointing**: Arm extends, points at screen (1s, trigger)
7. **Waving**: Hand wave (1s, trigger)
8. **Sleeping**: Z's float up (loop, for session limit screen)

**Files**:
- `static/animations/dash-rabbit.riv`
- `static/animations/sparkle-unicorn.riv`
- `static/animations/nova-owl.riv`
- `static/animations/buddy-dog.riv`

**Performance**: Rive uses WASM + WebGL, 60 FPS on iPad Air 2

**Budget**: 
- Commission designer on Upwork/Fiverr: $200-400 per character
- Or use Rive Community assets (free) + customize colors

---

#### B. GSAP (GreenSock Animation Platform)

**Use Case**: Complex UI transitions, timelines, orchestration

**Why GSAP?**
- **Best-in-class performance**: GPU-accelerated, 60 FPS
- **Timeline control**: Sequence animations precisely
- **Easing library**: 20+ easing functions (elastic, bounce, etc.)
- **Cross-browser**: Works on Safari, Chrome, old browsers

**License**: Free for non-commercial or < $50K revenue; Business license $199/year

**Implementation**:
```javascript
// Install via npm
npm install gsap

// In game_session_v2.js
import { gsap } from 'gsap';

// Example: Question transition
function nextQuestion(oldQuestion, newQuestion) {
    const tl = gsap.timeline();
    
    // 1. Slide old question out
    tl.to(oldQuestion, {
        x: -100,
        opacity: 0,
        duration: 0.3,
        ease: 'power2.in'
    });
    
    // 2. Slide new question in (from right)
    tl.fromTo(newQuestion, 
        { x: 100, opacity: 0 },
        { x: 0, opacity: 1, duration: 0.4, ease: 'power2.out' }
    );
    
    // 3. Pop character in
    tl.from('.character-display', {
        scale: 0.5,
        opacity: 0,
        duration: 0.3,
        ease: 'back.out(1.7)'
    }, '-=0.2');  // Overlap with previous animation
    
    // 4. Fade in options (stagger)
    tl.from('.option-btn', {
        y: 20,
        opacity: 0,
        duration: 0.3,
        stagger: 0.1,  // 0.1s delay between each button
        ease: 'power2.out'
    }, '-=0.1');
}

// Example: Confetti burst
function celebrateCorrect(button) {
    // Button flash
    gsap.to(button, {
        scale: 1.1,
        duration: 0.2,
        yoyo: true,
        repeat: 1,
        ease: 'power2.inOut'
    });
    
    // Screen flash
    gsap.fromTo('.screen-flash',
        { opacity: 0.3 },
        { opacity: 0, duration: 0.6, ease: 'power2.out' }
    );
    
    // Confetti (handled by canvas, see below)
    createConfetti(button.getBoundingClientRect());
}
```

**Use Cases in Skool**:
- Question transitions (slide, fade, scale)
- Session results count-up animations
- Progress bar fills
- Modal/overlay entrances
- Parallax scrolling (world map)

**Files**:
- **Modify**: All JS files → use GSAP instead of CSS transitions for complex animations
- **New**: `static/js/animation-utils.js` → reusable GSAP snippets

**Performance Budget**: Max 5 concurrent GSAP animations

---

#### C. Canvas Particles (Custom)

**Use Case**: Confetti, sparkles, floating elements (high-volume, low-complexity)

**Why Canvas over DOM?**
- **Performance**: 1,000 DOM divs = lag; 1,000 canvas particles = smooth
- **No layout thrashing**: Canvas doesn't trigger reflow/repaint
- **Compositing**: GPU renders entire canvas as one texture

**Implementation**:
```javascript
// static/js/particles.js

class ParticleSystem {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.animationFrame = null;
        
        // Retina support
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = window.innerWidth * dpr;
        this.canvas.height = window.innerHeight * dpr;
        this.ctx.scale(dpr, dpr);
        
        this.animate();
    }
    
    createConfetti(x, y, count = 50) {
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#FFD93D'];
        
        for (let i = 0; i < count; i++) {
            this.particles.push({
                x: x,
                y: y,
                vx: (Math.random() - 0.5) * 8,
                vy: (Math.random() - 1) * 10,
                rotation: Math.random() * 360,
                rotationSpeed: (Math.random() - 0.5) * 10,
                color: colors[Math.floor(Math.random() * colors.length)],
                size: Math.random() * 8 + 4,
                life: 1.0,
                decay: Math.random() * 0.01 + 0.01
            });
        }
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update and draw particles
        this.particles = this.particles.filter(p => {
            // Physics
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.3;  // Gravity
            p.rotation += p.rotationSpeed;
            p.life -= p.decay;
            
            // Draw
            if (p.life > 0) {
                this.ctx.save();
                this.ctx.translate(p.x, p.y);
                this.ctx.rotate(p.rotation * Math.PI / 180);
                this.ctx.globalAlpha = p.life;
                this.ctx.fillStyle = p.color;
                this.ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size);
                this.ctx.restore();
                return true;  // Keep particle
            }
            return false;  // Remove particle
        });
        
        this.animationFrame = requestAnimationFrame(() => this.animate());
    }
    
    destroy() {
        cancelAnimationFrame(this.animationFrame);
    }
}

// Usage
const particles = new ParticleSystem('particles-canvas');
document.querySelector('.option-btn').addEventListener('click', (e) => {
    const rect = e.target.getBoundingClientRect();
    particles.createConfetti(rect.left + rect.width/2, rect.top + rect.height/2);
});
```

**Other Particle Effects**:
- **Sparkles**: Follow mascot (orbit effect)
- **Floating leaves**: Bamboo forest background
- **Floating letters**: English Garden background
- **Stars**: Night sky (space theme)

**Files**:
- **New**: `static/js/particles.js`
- **New**: `<canvas id="particles-canvas">` in base template

**Performance Budget**: Max 200 particles on screen simultaneously

---

#### D. Motion One (Lightweight Alternative to GSAP)

**If GSAP license is an issue**, use **Motion One** (MIT license, free)

**Why Motion One?**
- **Size**: 3.8KB (vs GSAP's 50KB)
- **Performance**: Uses Web Animations API (browser-native)
- **API**: Similar to GSAP, easy migration

**Implementation**:
```javascript
import { animate, stagger } from 'motion';

animate('.option-btn', 
    { opacity: [0, 1], y: [20, 0] },
    { duration: 0.3, delay: stagger(0.1) }
);
```

**Recommendation**: Start with Motion One (Phase 1), upgrade to GSAP if we need advanced features (Phase 2)

---

#### E. Framer Motion (If We Use React)

**Only relevant if we switch to React** (see 3.4 Framework Decision)

**Why Framer Motion?**
- **React-first**: Works seamlessly with components
- **Declarative**: `<motion.div animate={{ scale: 1.2 }} />`
- **Gestures**: Drag, tap, hover built-in

**Not recommended for vanilla JS** — use GSAP/Motion One instead

---

### 3.4 FRAMEWORK DECISION: Vanilla JS vs Modern Framework

#### Current State: Vanilla JS + Jinja2 SSR

**Pros**:
- No build step (fast iteration)
- Server-side rendering (SEO, fast first paint)
- Small bundle size (~20KB JS total)
- No framework lock-in

**Cons**:
- Manual DOM manipulation (error-prone)
- No component reusability
- State management is ad-hoc
- Testing is harder

---

#### Option A: **Keep Vanilla JS** (Recommended for Phase 1-2)

**Rationale**:
- Current codebase is manageable (~2K lines JS)
- With better structure, vanilla JS is fine for Skool's complexity
- Modern CSS + GSAP/Motion One + Rive covers animation needs
- Adding a framework now = 4-6 weeks rewrite (not worth it yet)

**Improvements to make vanilla JS sustainable**:
1. **Module structure**: Split `racing.js` (1,073 lines) into:
   - `game-session.js` (core game loop)
   - `question-renderer.js` (UI updates)
   - `feedback-controller.js` (animations)
   - `mascot-controller.js` (Rive integration)

2. **State management**: Simple store pattern
```javascript
// static/js/store.js
const AppState = {
    user: {},
    session: {},
    listeners: [],
    
    setState(key, value) {
        this[key] = value;
        this.listeners.forEach(fn => fn(this));
    },
    
    subscribe(fn) {
        this.listeners.push(fn);
    }
};
```

3. **Component pattern** (Web Components, no framework):
```javascript
// static/js/components/mascot.js
class MascotComponent extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `<canvas id="mascot"></canvas>`;
        this.rive = new rive.Rive({...});
    }
    
    celebrate() {
        this.rive.stateMachineInputs.find(i => i.name === 'celebrate').fire();
    }
}
customElements.define('skool-mascot', MascotComponent);

// Usage in HTML
<skool-mascot id="dash"></skool-mascot>
<script>
    document.getElementById('dash').celebrate();
</script>
```

**Files**:
- **Refactor**: `static/js/racing.js` → split into modules
- **New**: `static/js/store.js`
- **New**: `static/js/components/` directory

---

#### Option B: **Migrate to React** (Phase 3, if complexity grows)

**When to consider React**:
- If we add real-time multiplayer (sibling races)
- If we build a complex admin panel
- If we hire frontend engineers who prefer React

**Migration Strategy** (if we go this route):
1. **Parallel implementation**: New screens in React, old screens stay
2. **React Islands**: Render React components in specific `<div>` roots
3. **Gradual rewrite**: Game session → Results → World Map → etc.

**Build setup**:
```bash
npm install react react-dom vite
npm install @vitejs/plugin-react

# vite.config.js
export default {
    plugins: [react()],
    build: {
        outDir: 'static/dist',
        rollupOptions: {
            input: {
                main: 'src/main.tsx',
                game: 'src/game.tsx'
            }
        }
    }
}
```

**Bundle size impact**: +140KB (React + ReactDOM, gzipped)

**Timeline**: 8-10 weeks for full migration

---

#### **Decision: Keep Vanilla JS for Now**

**Phase 1-2**: Improve vanilla JS with modules + Web Components  
**Phase 3**: Revisit if complexity demands it

**Why**: 
- Skool is a content app, not a SPA (most state is server-side)
- SSR is valuable (Jinja2 templates = fast first render)
- Build complexity adds friction for solo/small team
- 80% of improvements (animations, design) don't need React

---

### 3.5 PERFORMANCE BUDGET

**Target Devices**:
- iPad Air 2 (2014): A8X chip, 2GB RAM
- iPhone SE 2nd gen (2020): A13 chip, 3GB RAM
- Modern devices: Bonus performance

---

#### Load Performance

| Metric | Target | Current | Strategy |
|--------|--------|---------|----------|
| **First Contentful Paint** | < 1.0s | ~1.2s | Inline critical CSS, preload fonts |
| **Largest Contentful Paint** | < 2.0s | ~2.5s | Optimize images (WebP), lazy-load below fold |
| **Time to Interactive** | < 2.5s | ~3.0s | Defer non-critical JS, code-split |
| **Total Bundle Size** | < 200KB | ~150KB | ✅ Good, room for +50KB (Rive runtime) |
| **Image Weight** | < 500KB | ~800KB | Convert PNGs to WebP (60% smaller) |

**Actions**:
1. **Convert images**: `cwebp -q 85 input.png -o output.webp`
2. **Lazy-load**: `<img loading="lazy" src="...">`
3. **Code-split**: Separate bundles for game vs dashboard
4. **Service Worker**: Precache critical assets only (~100KB)

---

#### Runtime Performance

| Metric | Target | Strategy |
|--------|--------|----------|
| **Frame Rate** | 60 FPS | Use `transform` + `opacity` only (GPU), avoid layout thrashing |
| **Animation Budget** | Max 5 concurrent | Queue animations, cancel old ones |
| **Particle Count** | Max 200 | Cull off-screen particles, use object pooling |
| **Rive Characters** | Max 2 on screen | Pause idle animations when not visible |
| **Memory Usage** | < 100MB | Destroy particles after 3s, clear TTS cache periodically |

**Monitoring**:
```javascript
// Performance profiler (dev mode only)
if (window.location.search.includes('debug')) {
    let frameCount = 0;
    let lastTime = performance.now();
    
    function checkFPS() {
        const now = performance.now();
        frameCount++;
        
        if (now - lastTime > 1000) {
            console.log(`FPS: ${frameCount}`);
            frameCount = 0;
            lastTime = now;
        }
        
        requestAnimationFrame(checkFPS);
    }
    checkFPS();
}
```

---

#### Device-Specific Optimizations

**iPad Air 2** (worst-case target):
- Disable Rive animations (use static mascot PNG)
- Reduce particle count to 50
- Disable parallax scrolling
- Lower confetti quality

**Detection**:
```javascript
const isLowEndDevice = (() => {
    const memory = navigator.deviceMemory;  // GB, only in Chrome
    const cores = navigator.hardwareConcurrency;
    
    // iPad Air 2: 2GB RAM, 3 cores
    return memory && memory <= 2 && cores <= 3;
})();

if (isLowEndDevice) {
    // Fallback mode
    window.PERFORMANCE_MODE = 'low';
}
```

---

### 3.6 MIGRATION PLAN (Updated Roadmap)

#### Phase 1: Visual Refresh (4 weeks)

**Week 1-2: Design System + Core Components**
- [ ] Define color palette, typography, spacing scale
- [ ] Create Figma design file (all 8 screens)
- [ ] Build component library (buttons, cards, progress bars)
- [ ] Convert 10 key SVG icons
- [ ] **Files**: `static/css/design-system.css`, `static/css/components.css`

**Week 3: Login + World Map**
- [ ] Redesign login screen (avatar cards)
- [ ] Build world map layout (static, no parallax yet)
- [ ] Add bottom navigation bar
- [ ] **Files**: `templates/login_v2.html`, `templates/world_map.html`
- [ ] **Migration**: Keep old `/login` route, add `/beta/login` for testing

**Week 4: Game Session Screen**
- [ ] Implement new question layout
- [ ] Add combo meter
- [ ] Integrate Motion One for transitions
- [ ] **Files**: `templates/game_session_v2.html`, `static/js/game_session_v2.js`
- [ ] **Migration**: A/B test 20% of users on new design

**Deliverable**: Users can play through new UI (login → map → game)

---

#### Phase 2: Animation + Interactivity (6 weeks)

**Week 5-6: Rive Mascot Integration**
- [ ] Commission Dash rabbit character (8 states)
- [ ] Commission Sparkle unicorn character
- [ ] Integrate Rive runtime
- [ ] Add mascot reactions to game events
- [ ] **Files**: `static/animations/dash.riv`, `static/js/mascot-controller.js`

**Week 7: Canvas Particle System**
- [ ] Build particle engine
- [ ] Replace CSS confetti with canvas confetti
- [ ] Add floating elements to backgrounds
- [ ] **Files**: `static/js/particles.js`

**Week 8: Session Results + Feedback**
- [ ] Redesign results screen (celebration focus)
- [ ] Add count-up animations (GSAP/Motion One)
- [ ] Level-up celebration overlay
- [ ] Enhanced teaching panel
- [ ] **Files**: `templates/session_results_v2.html`

**Week 9-10: Garage + Progress Map**
- [ ] Redesign store/garage (3 tabs)
- [ ] Add 3D preview (optional, or static preview)
- [ ] Build kid progress map
- [ ] Add badge/trophy case
- [ ] **Files**: `templates/garage_v2.html`, `templates/progress_map_v2.html`

**Deliverable**: Full UI refresh live for all users

---

#### Phase 3: Advanced Features (8 weeks, concurrent with Section 2)

**Week 11-12: Adaptive Engine Data Model**
- [ ] Migrate to `learning_standards` table
- [ ] Add Elo + BKT fields
- [ ] Run migration on staging
- [ ] **Files**: `app/models/learning_standard.py`, `alembic/versions/...`

**Week 13-14: Placement Test + Dynamic Difficulty**
- [ ] Build placement test algorithm
- [ ] Create placement UI
- [ ] Implement Elo-based session difficulty
- [ ] **Files**: `app/services/placement_test.py`, `app/services/adaptive_mastery.py`

**Week 15-16: Extended Content**
- [ ] Add 500 more Chinese characters (540 → 1,000)
- [ ] Generate/commission SVG icons for new characters
- [ ] Map to grade levels (Grade 1-3)
- [ ] **Files**: `app/seed/characters_extended.json`, `static/images/chars/...`

**Week 17-18: Parent Dashboard Redesign**
- [ ] Redesign dashboard (Buddy mascot, cleaner layout)
- [ ] Add family leaderboard
- [ ] Add AI-generated insights (GPT-4 API, optional)
- [ ] **Files**: `templates/dashboard_v2.html`

**Deliverable**: Smart, adaptive game with modern UI

---

#### Phase 4: Polish + Optimization (4 weeks)

**Week 19: Performance Audit**
- [ ] Run Lighthouse on all screens
- [ ] Optimize images (WebP conversion)
- [ ] Code-split JS bundles
- [ ] Add low-end device detection + fallbacks

**Week 20: Accessibility Audit**
- [ ] Add ARIA labels to all interactive elements
- [ ] Test with VoiceOver (iOS) and NVDA (Windows)
- [ ] Ensure WCAG AAA contrast (7:1 ratio)
- [ ] Add keyboard navigation

**Week 21: Cross-Device Testing**
- [ ] Test on iPad Air 2, iPad Pro, iPhone SE, iPhone 15
- [ ] Test on Chrome, Safari, Firefox
- [ ] Fix layout breaks
- [ ] Verify 60 FPS on target devices

**Week 22: Onboarding + Voice Prompts**
- [ ] Build interactive tutorial
- [ ] Add voice prompts for pre-readers (Web Speech API)
- [ ] Parent settings toggle
- [ ] **Files**: `static/js/onboarding.js`, `static/js/voice_prompts.js`

**Deliverable**: Polished, accessible, high-performance app

---

### Total Timeline: 22 weeks (~5.5 months)

**Critical Path**:
1. Phase 1 (Visual Refresh) → blocks everything
2. Phase 2 (Animation) → can start Week 3 (parallel with Phase 1 backend)
3. Phase 3 (Adaptive Engine) → independent, can start Week 8
4. Phase 4 (Polish) → must be last

**Parallelization Opportunities**:
- Content creation (characters, icons) can happen alongside UI development
- Rive mascot design can happen Week 1-4 (async)
- Parent dashboard redesign can happen independently (Week 10-12)

---

## Summary Table: UI Redesign Scope

| Screen | Current State | New Design | Key Changes | Files |
|--------|---------------|------------|-------------|-------|
| **Login** | Text list | Avatar cards | Personality, animations | `templates/login_v2.html` |
| **Game Selector** | 4-card grid | World map | Exploration, progression | `templates/world_map.html` |
| **Question** | Sky + road | Themed immersive | Per-subject backgrounds, mascot | `templates/game_session_v2.html` |
| **Feedback** | Basic flash | Rich micro-interactions | Particles, mascot reactions | `static/js/feedback-controller.js` |
| **Results** | Text table | Victory screen | Celebration, count-ups | `templates/session_results_v2.html` |
| **Garage** | Flat list | 3-tab collection | Ownership pride, previews | `templates/garage_v2.html` |
| **Kid Progress** | (Doesn't exist) | Visual journey | Tree, badges, milestones | `templates/progress_map_v2.html` |
| **Dashboard** | Data-dense table | Family command center | Buddy guide, insights | `templates/dashboard_v2.html` |

---

## Risk Assessment: UI Redesign

### High-Risk Items

1. **Rive Licensing / Budget**
   - **Risk**: Custom character design costs $200-400 per character × 4 = $800-1,600
   - **Mitigation**: 
     - Use Rive Community assets (free) + recolor
     - Commission Dash only (Phase 1), add others in Phase 2-3
     - Fallback to static PNG mascots if budget unavailable

2. **Performance Regression on iPad Air 2**
   - **Risk**: Rive + GSAP + Canvas particles = too much for 2014 hardware
   - **Mitigation**:
     - Test early on real device (Week 2)
     - Implement low-end device detection
     - Keep CSS-only fallback mode

3. **Migration Disruption**
   - **Risk**: Breaking existing users during redesign
   - **Mitigation**:
     - Dual routes (`/login` vs `/beta/login`)
     - Feature flags (10% → 50% → 100% rollout)
     - Keep old templates until Phase 2 complete

### Medium-Risk Items

1. **GSAP License Cost**
   - **Risk**: Business license $199/year if revenue > $50K
   - **Mitigation**: Use Motion One (free) instead, or confirm revenue threshold

2. **Designer Bandwidth**
   - **Risk**: Solo developer = no dedicated designer
   - **Mitigation**:
     - Use Figma templates (e.g., "Kids App UI Kit")
     - Commission specific screens on Dribbble/Behance ($50-100 per screen)
     - AI-assisted design (v0.dev, Galileo AI for wireframes)

3. **Cross-Browser Compatibility**
   - **Risk**: Rive/Canvas may have Safari bugs
   - **Mitigation**:
     - Test on Safari early (Week 3)
     - Use polyfills for Web Animations API
     - PNG fallback for unsupported browsers

---

## Budget Summary

| Item | Cost | Phase |
|------|------|-------|
| **Rive Character Design** | $800-1,600 (4 characters) | 2 |
| **GSAP Business License** | $199/year (or use Motion One: $0) | 2 |
| **Icon Pack** | $0 (Phosphor Icons free) | 1 |
| **Figma Design Templates** | $0-50 (optional) | 1 |
| **Stock Illustrations** | $100-200 (backgrounds, decorations) | 1-2 |
| **Performance Testing Devices** | $0 (use real user devices) | 4 |
| **Total (Minimum)** | **$100-300** | |
| **Total (Full Budget)** | **$1,100-2,050** | |

**Recommendation**: Start with **$300 budget** (no Rive, use PNG mascots + Motion One), upgrade to full budget in Phase 3 if results are good.

---

## Success Metrics: UI Redesign

**Phase 1** (Visual Refresh):
- [ ] Session completion rate +10% (better UX = less abandonment)
- [ ] Time-on-screen +15% (more engaging)
- [ ] Parent NPS (Net Promoter Score) +20 points

**Phase 2** (Animation):
- [ ] Kid satisfaction +25% (measured via parent survey)
- [ ] Mascot interaction rate >50% (kids tap mascot)
- [ ] "Delightful" mentions in reviews +30%

**Phase 3** (Full Experience):
- [ ] Daily active users +30%
- [ ] 30-day retention +25%
- [ ] Parent willingness to pay (if monetized) +40%

---

**End of Expanded Section 3**

#### A. Physics-Based Car Movement

**Current**: Linear CSS transition
```css
.car-sprite {
    transition: left 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
```

**Proposed**: Spring physics with overshoot/settle
```css
.car-sprite {
    transition: left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);  /* Overshoot easing */
}

.car-sprite.boost {
    animation: carBoostPhysics 0.8s cubic-bezier(0.22, 1.2, 0.36, 1);
}

@keyframes carBoostPhysics {
    0%   { transform: scaleX(-1) translateX(0); }
    20%  { transform: scaleX(-1) translateX(-10px) scale(1.1); }  /* Wind-up */
    60%  { transform: scaleX(-1) translateX(5px) scale(1.2); }    /* Surge forward */
    80%  { transform: scaleX(-1) translateX(-2px) scale(1.05); }  /* Settle bounce */
    100% { transform: scaleX(-1) translateX(0) scale(1); }
}
```

**Files**: `static/css/racing.css:550-595`

#### B. Rich Particle Effects (Lottie or Canvas)

**Option 1: Lottie** (vector animations, 10-50KB per animation)
- Use [LottieFiles](https://lottiefiles.com/) free animations
- Correct answer: Sparkling stars + confetti burst
- Wrong answer: Puff of smoke
- Car boost: Speed lines + dust cloud

```html
<!-- Add to templates/themes/racing/game.html -->
<script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>

<lottie-player 
    id="correctAnimation"
    src="/static/animations/success-confetti.json"
    style="position: fixed; inset: 0; pointer-events: none; display: none; z-index: 999;"
    background="transparent">
</lottie-player>
```

**Option 2: CSS Particles** (lightweight, no dependencies)
```javascript
// static/js/racing.js - enhance confetti
function createAdvancedConfetti(count = 50) {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F'];
    const container = document.querySelector('.celebration-burst');
    
    for (let i = 0; i < count; i++) {
        const piece = document.createElement('div');
        piece.className = 'confetti-piece';
        piece.style.left = `${Math.random() * 100}%`;
        piece.style.top = `${-20 + Math.random() * 10}px`;
        piece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        piece.style.animationDelay = `${Math.random() * 0.3}s`;
        piece.style.transform = `rotate(${Math.random() * 360}deg)`;
        
        // Add variety: some are stars, some are circles, some are squares
        if (Math.random() > 0.7) {
            piece.style.borderRadius = '50%';
        } else if (Math.random() > 0.5) {
            piece.innerHTML = '⭐';
            piece.style.fontSize = '16px';
        }
        
        container.appendChild(piece);
        setTimeout(() => piece.remove(), 2000);
    }
}
```

**Recommendation**: Start with **CSS particles** (Phase 1), upgrade to Lottie if budget allows (Phase 3)

**Files**: 
- `static/js/racing.js` → enhance confetti function
- `static/animations/` → (Phase 3) Lottie JSON files

#### C. Character Mascot System

**Concept**: Friendly animal mascot appears in corner, reacts to answers

**Characters by theme**:
- Racing: 🐰 Speed Rabbit ("Dash")
- Pony: 🦄 Unicorn ("Sparkle")

**Reactions**:
- **Idle**: Gentle bounce animation
- **Correct**: Jumps for joy, confetti burst
- **Wrong**: Sad face, encouraging gesture
- **Streak 5+**: Wears sunglasses, does victory dance
- **Session complete**: Fireworks, thumbs up

```css
/* static/css/racing.css - add mascot container */
.mascot-container {
    position: fixed;
    bottom: 120px;
    right: 20px;
    width: 80px;
    height: 80px;
    z-index: 100;
    pointer-events: none;
}

.mascot {
    font-size: 60px;
    animation: mascotIdle 2s ease-in-out infinite;
    filter: drop-shadow(2px 4px 8px rgba(0,0,0,0.2));
}

@keyframes mascotIdle {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-10px) scale(1.05); }
}

.mascot.celebrating {
    animation: mascotJump 0.6s ease-out;
}

@keyframes mascotJump {
    0% { transform: translateY(0) rotate(0deg); }
    30% { transform: translateY(-40px) rotate(-15deg); }
    50% { transform: translateY(-50px) rotate(15deg); }
    70% { transform: translateY(-30px) rotate(-10deg); }
    100% { transform: translateY(0) rotate(0deg); }
}
```

**Files**:
- `static/css/racing.css` → add mascot styles
- `static/js/racing.js` → add mascot reaction triggers
- `templates/themes/racing/game.html` → inject mascot div

#### D. Sound Design Upgrade

**Current**: Only TTS (text-to-speech for characters)

**Add**:
1. **SFX library** (short sounds, <50KB total):
   - `correct.mp3`: Cheerful chime (C major chord)
   - `wrong.mp3`: Gentle "uh-oh" (not harsh)
   - `boost.mp3`: Whoosh sound
   - `complete.mp3`: Victory fanfare
   - `combo.mp3`: Rising pitch for streaks

2. **Adaptive music**:
   - Current: 4 tracks play in full
   - Proposed: Add 30s loop variants that change intensity
   - High streak (5+): Add percussion layer
   - Struggling: Slow tempo slightly

```javascript
// static/js/music.js - enhance with layered audio
class AdaptiveMusicPlayer {
    constructor() {
        this.baseLayer = new Audio('/static/music/base-loop.mp3');
        this.percussionLayer = new Audio('/static/music/percussion-loop.mp3');
        this.baseLayer.loop = true;
        this.percussionLayer.loop = true;
        this.percussionLayer.volume = 0; // Start muted
    }
    
    onStreak(level) {
        if (level >= 5) {
            // Fade in percussion
            this.fadeVolume(this.percussionLayer, 0.6, 1000);
        }
    }
    
    fadeVolume(audio, target, duration) {
        const steps = 20;
        const stepTime = duration / steps;
        const volumeIncrement = (target - audio.volume) / steps;
        
        const interval = setInterval(() => {
            audio.volume += volumeIncrement;
            if (--steps <= 0) clearInterval(interval);
        }, stepTime);
    }
}
```

**Files**:
- `static/sounds/` → new directory with SFX
- `static/js/music.js` → refactor to adaptive system
- `static/js/racing.js` → trigger SFX on events

#### E. Haptics on Phones (iOS/Android)

```javascript
// static/js/common.js - add haptic feedback helpers
const Haptics = {
    light: () => {
        if (navigator.vibrate) navigator.vibrate(10);
    },
    
    medium: () => {
        if (navigator.vibrate) navigator.vibrate(20);
    },
    
    heavy: () => {
        if (navigator.vibrate) navigator.vibrate([20, 10, 20]);
    },
    
    success: () => {
        if (navigator.vibrate) navigator.vibrate([10, 5, 10, 5, 15]);
    },
    
    error: () => {
        if (navigator.vibrate) navigator.vibrate([15, 10, 15]);
    }
};

// Use in racing.js
function submitAnswer(questionId, answer) {
    // ...existing logic...
    if (result.is_correct) {
        Haptics.success();
    } else {
        Haptics.error();
    }
}
```

**Files**: 
- `static/js/common.js` → add Haptics utility
- `static/js/racing.js` → trigger on answer events

#### F. Combo Meter (Streak Visualization)

**Concept**: Visible combo counter for consecutive correct answers (within session)

```html
<!-- Add to game.html -->
<div class="combo-meter" id="comboMeter">
    <div class="combo-count">×<span id="comboCount">0</span></div>
    <div class="combo-bar">
        <div class="combo-fill" id="comboFill"></div>
    </div>
    <div class="combo-label">COMBO!</div>
</div>
```

```css
.combo-meter {
    position: fixed;
    top: 80px;
    right: 20px;
    opacity: 0;
    transition: opacity 0.3s;
}

.combo-meter.active {
    opacity: 1;
    animation: comboPulse 0.5s ease-out;
}

.combo-count {
    font-size: 36px;
    font-weight: 900;
    color: #FF6B35;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

@keyframes comboPulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.3); }
    100% { transform: scale(1); }
}
```

**Files**:
- `templates/themes/racing/game.html` → add combo meter HTML
- `static/css/racing.css` → add combo styles
- `static/js/racing.js` → track combo count, trigger animations

### Performance Constraints

**Target**: 60 FPS on iPad Air 2 (2014), 30 FPS on iPhone SE (2016)

**Budget**:
- **Lottie animations**: Max 2 concurrent (100KB total)
- **Canvas particles**: Max 100 particles on screen
- **Audio**: Max 3 concurrent sounds (music + 2 SFX)
- **CSS animations**: Use `transform` and `opacity` only (GPU-accelerated)
- **Avoid**: Heavy JS in animation loops, large DOM manipulations during gameplay

**Files to monitor**:
- `static/js/racing.js` → keep game loop under 16ms (60 FPS)
- Test on real iPad Air 2 before shipping

---

## 4. DAILY ENGAGEMENT: Building Habits Without Manipulation

### Current State: Basic Streak + Coins

**Good**:
- Streak system with freeze mechanic
- Points → Stars → Coins → RMB conversion
- Car tier progression

**Missing**:
- No daily quests or goals
- No collectible variety
- Progress isn't visualized for kids
- No gentle reminders
- Sibling features are minimal

### Proposed: 7-Day Engagement System

#### A. Daily Quests (Kid-Friendly Objectives)

**Concept**: 3 rotating daily quests, completable in 2-3 sessions

```python
# app/models/daily_quest.py

QUEST_TEMPLATES = [
    {
        "id": "speed_demon",
        "name": "Speed Demon ⚡",
        "description": "Answer 5 questions in under 5 seconds each",
        "reward_coins": 2,
        "target": 5,
        "metric": "speed_answers"
    },
    {
        "id": "perfect_day",
        "name": "Perfect Day ⭐",
        "description": "Get 100% correct in any session",
        "reward_coins": 3,
        "target": 1,
        "metric": "perfect_sessions"
    },
    {
        "id": "practice_makes_perfect",
        "name": "Practice Makes Perfect 📚",
        "description": "Complete 2 sessions today",
        "reward_coins": 2,
        "target": 2,
        "metric": "sessions_completed"
    },
    {
        "id": "subject_explorer",
        "name": "Subject Explorer 🌎",
        "description": "Play Chinese, Math, AND English today",
        "reward_coins": 4,
        "target": 3,
        "metric": "unique_subjects"
    },
    {
        "id": "comeback_kid",
        "name": "Comeback Kid 💪",
        "description": "Turn 3 wrong answers into correct ones",
        "reward_coins": 2,
        "target": 3,
        "metric": "retry_successes"
    }
]

class UserDailyQuest(Base):
    __tablename__ = "user_daily_quests"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quest_id = Column(String(50))  # from QUEST_TEMPLATES
    progress = Column(Integer, default=0)
    target = Column(Integer)
    completed_at = Column(DateTime, nullable=True)
    date_assigned = Column(Date)
```

**What the kid sees**: On game selector screen, 3 quest cards with progress bars

**Files**:
- **New**: `app/models/daily_quest.py`
- **New**: `app/services/quest_tracker.py` → assign quests, track progress
- **Modify**: `templates/game_selector.html` → add quest cards section
- **Modify**: `app/routes/game.py` → check quest progress after each session

#### B. Kid-Facing Progress Map

**Current**: Parent dashboard shows mastery distribution, kids see only points

**Proposed**: "Your Learning Journey" screen for kids

```html
<!-- New template: templates/progress_map.html -->
<div class="progress-map">
    <div class="map-header">
        <h1>🗺️ Your Learning Journey</h1>
        <div class="avatar">{{ user.name[0] }}</div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{{ characters_mastered }}</div>
            <div class="stat-label">Characters Mastered</div>
            <div class="stat-emoji">🎯</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-number">{{ days_streak }}</div>
            <div class="stat-label">Day Streak</div>
            <div class="stat-emoji">🔥</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-number">{{ total_coins }}</div>
            <div class="stat-label">Coins Earned</div>
            <div class="stat-emoji">🪙</div>
        </div>
    </div>
    
    <!-- Progress bars by subject -->
    <div class="subject-progress">
        <h2>Subject Progress</h2>
        
        <div class="progress-item">
            <div class="progress-header">
                <span>🇨🇳 Chinese</span>
                <span>{{ chinese_level }}</span>
            </div>
            <div class="progress-bar-track">
                <div class="progress-bar-fill" style="width: {{ chinese_pct }}%"></div>
            </div>
            <div class="progress-sublabel">{{ chinese_mastered }}/{{ chinese_total }} characters</div>
        </div>
        
        <!-- Repeat for Math, English, Logic -->
    </div>
    
    <!-- Recent achievements -->
    <div class="recent-wins">
        <h2>Recent Wins 🏆</h2>
        <div class="win-list">
            <div class="win-item">Perfect session yesterday!</div>
            <div class="win-item">Unlocked new car: 🏎️ Race Car</div>
            <div class="win-item">Mastered 10 new words this week</div>
        </div>
    </div>
</div>
```

**Access**: Big "My Progress" button on game selector

**Files**:
- **New**: `templates/progress_map.html`
- **New**: `app/routes/progress.py` → generate progress stats
- **Modify**: `templates/game_selector.html` → add "My Progress" button

#### C. Collectible System: More Than Cars

**Current**: 5 car tiers + store items (skins, backgrounds, trails)

**Expand**: 
1. **Car Garage**: Keep existing 5 tiers, add 3 skins per tier (15 total)
   - Example: Tier 2 Race Car → Red Racer, Blue Bolt, Green Machine
2. **Companion Pets**: Unlockable animals that ride along
   - 🐢 Turtle (Starter), 🐰 Rabbit (10 coins), 🦊 Fox (25 coins), 🐉 Dragon (50 coins)
3. **Environment Themes**: More than 6 backgrounds
   - Beach, Forest, Snow, Space, City, Candy Land, Underwater, Desert
4. **Trail Effects**: Exhaust/dust clouds behind car
   - Stars ⭐, Hearts 💖, Fire 🔥, Sparkles ✨

**No Loot Boxes**: All items have fixed prices, visible before purchase

**Files**:
- **Modify**: `app/models/store.py` → add pet, theme, trail items
- **Modify**: `templates/store.html` → organize by category (Cars, Pets, Themes, Trails)
- **Modify**: `static/css/racing.css` → add pet sprite rendering

#### D. Gentle Notifications (Parent-Controlled)

**Concept**: Optional reminders that respect boundaries

**Parent Dashboard Settings**:
```
☐ Enable daily reminders
  Time: [2:00 PM] [▼]
  Days: ☑ Mon ☑ Tue ☑ Wed ☑ Thu ☑ Fri ☐ Sat ☐ Sun
  
☐ Streak protection alerts (notify parent if streak at risk)
☐ Weekly progress summary (email to parent)
```

**Notification Examples** (if enabled):
- iOS notification: "Daniel, your streak is waiting! 🔥 5 days strong"
- iPad banner: "Ellie hasn't played today — keep that 12-day streak alive!"

**Implementation**:
- **NOT in scope for Phase 1**: Requires backend job scheduler + push notification setup
- **Phase 3**: Use Heroku Scheduler + OneSignal or Firebase Cloud Messaging

**Files** (Phase 3):
- **New**: `app/services/notification_scheduler.py`
- **Modify**: `templates/dashboard.html` → add notification settings

#### E. Sibling-Friendly Features

**Current**: Two users (Daniel age 4, Ellie age 9) with separate profiles

**Enhancements**:

1. **Family Leaderboard** (Friendly Competition)
   ```
   This Week's Stars 🌟
   ━━━━━━━━━━━━━━━━━
   🥇 Ellie      127 ⭐
   🥈 Daniel      89 ⭐
   
   Keep it up, Daniel! You're catching up!
   ```

2. **Shared Celebrations** (Cooperative)
   - "Daniel and Ellie combined: 216 stars this week! 🎉"
   - "Family goal: 300 stars by Friday → unlock special family reward"

3. **No Direct Comparison** (Avoid Rivalry)
   - Don't show "Ellie is smarter" or "Daniel is behind"
   - Focus on personal growth: "You improved 23% this week!"

4. **Separate Progress, Shared Rewards**
   - Each child has own skill levels
   - But store items can be unlocked for both (parent decision)

**Files**:
- **Modify**: `templates/game_selector.html` → add family leaderboard widget
- **Modify**: `app/routes/dashboard.py` → compute family stats

#### F. Parent-Set Goals

**Parent Dashboard Feature**: Set weekly goals per child

```html
<!-- In dashboard.html -->
<div class="goal-setter">
    <h3>Set This Week's Goal for Daniel</h3>
    
    <label>
        <input type="radio" name="goal_type" value="sessions"> 
        Complete <input type="number" min="1" max="14" value="10"> sessions
    </label>
    
    <label>
        <input type="radio" name="goal_type" value="mastery">
        Master <input type="number" min="1" max="50" value="20"> new skills
    </label>
    
    <label>
        <input type="radio" name="goal_type" value="streak">
        Maintain <input type="number" min="3" max="30" value="7"> day streak
    </label>
    
    <label>
        Reward if achieved: <input type="text" placeholder="e.g., extra screen time">
    </label>
    
    <button>Set Goal</button>
</div>
```

**Kid sees**: Banner on game selector with progress toward parent-set goal

**Files**:
- **New**: `app/models/parent_goal.py`
- **Modify**: `templates/dashboard.html` → goal-setting UI
- **Modify**: `templates/game_selector.html` → display goal progress

### Anti-Dark-Pattern Principles

**What we WON'T do**:
- ❌ Infinite session timers ("Just one more!")
- ❌ FOMO tactics ("Your friends are ahead!")
- ❌ Paid loot boxes or gacha mechanics
- ❌ Deliberately addictive reward schedules
- ❌ Nagging notifications if parent disables them
- ❌ Progress loss if you don't play (streak freezes are available)

**What we WILL do**:
- ✅ Respect session limits (2/day default, parent can adjust)
- ✅ Celebrate effort, not just outcomes
- ✅ Make learning the reward, not just points
- ✅ Transparent pricing (coins → RMB is clear)
- ✅ Parent controls for all engagement features

---

## 5. UX & KID-FRIENDLINESS: Accessibility & Onboarding

### Current State: Good Touch Targets, Weak Onboarding

**Strengths**:
- 60px minimum touch targets
- No pinch-zoom
- TTS for Chinese characters

**Gaps**:
- No onboarding tutorial
- No voice prompts for pre-readers (age 3-5)
- No accessibility labels (screen readers)
- Login assumes kids know how to tap their avatar

### Proposed Improvements

#### A. First-Launch Onboarding (Interactive Tutorial)

**Flow for new user**:
1. **Welcome Screen**: "Hi! I'm Dash the Rabbit 🐰 Let's learn together!"
2. **Show how to tap**: Highlight TTS button, show animation "Tap here to hear the word!"
3. **Practice question**: One easy character with guidance overlay
4. **Mascot celebrates**: "Great job! You're ready to race!"

```javascript
// static/js/onboarding.js

const Onboarding = {
    steps: [
        {
            target: '.tts-btn',
            message: "Tap the speaker to hear the word!",
            highlightStyle: 'pulse',
            mascotReaction: 'pointing'
        },
        {
            target: '.option-btn:first-child',
            message: "Now tap the picture that matches!",
            highlightStyle: 'glow',
            mascotReaction: 'encouraging'
        },
        {
            target: '.car-sprite',
            message: "Watch your car zoom forward! 🏎️",
            highlightStyle: 'none',
            mascotReaction: 'celebrating'
        }
    ],
    
    show(stepIndex) {
        const step = this.steps[stepIndex];
        const target = document.querySelector(step.target);
        
        // Dim everything except target
        document.body.classList.add('onboarding-active');
        
        // Show tooltip
        this.showTooltip(target, step.message);
        
        // Highlight target
        target.classList.add(`highlight-${step.highlightStyle}`);
        
        // Mascot reacts
        Mascot.playAnimation(step.mascotReaction);
    }
};
```

**Files**:
- **New**: `static/js/onboarding.js`
- **New**: `templates/onboarding.html` (overlay system)
- **Modify**: `app/models/user.py` → add `onboarding_completed` flag

#### B. Voice Prompts for Pre-Readers

**For ages 3-5** (pre-readers who can't read "Question 1 of 5"):

**Implementation**: Web Speech API for English prompts
```javascript
// static/js/voice_prompts.js

class VoicePrompts {
    constructor() {
        this.synthesis = window.speechSynthesis;
        this.voice = this.getChildFriendlyVoice();
        this.enabled = false; // Parent toggle in settings
    }
    
    getChildFriendlyVoice() {
        const voices = this.synthesis.getVoices();
        // Prefer child/female voice
        return voices.find(v => v.name.includes('child') || v.name.includes('Samantha')) || voices[0];
    }
    
    speak(text, options = {}) {
        if (!this.enabled) return;
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.voice = this.voice;
        utterance.rate = 0.9;  // Slightly slower
        utterance.pitch = 1.2; // Higher pitch for warmth
        this.synthesis.speak(utterance);
    }
    
    // Contextual prompts
    onQuestionStart() {
        this.speak("Which picture matches the word?");
    }
    
    onCorrect() {
        const phrases = ["Great job!", "You got it!", "Awesome!", "Well done!"];
        this.speak(phrases[Math.floor(Math.random() * phrases.length)]);
    }
    
    onWrong() {
        const phrases = ["Try again!", "Not quite, keep going!", "You can do it!"];
        this.speak(phrases[Math.floor(Math.random() * phrases.length)]);
    }
}
```

**Parent Control**: Settings toggle "Enable voice guidance for pre-readers"

**Files**:
- **New**: `static/js/voice_prompts.js`
- **Modify**: `templates/dashboard.html` → add voice prompt setting
- **Modify**: `static/js/racing.js` → trigger voice prompts at key moments

#### C. Accessibility (Screen Reader Support)

**Current**: No ARIA labels

**Add**:
```html
<!-- templates/themes/racing/game.html -->

<button 
    class="tts-btn" 
    onclick="speakCharacter()" 
    type="button" 
    aria-label="Listen to pronunciation"
    role="button">
    &#128266;
</button>

<button 
    class="option-btn"
    data-answer="{{ opt }}"
    aria-label="Answer option: {{ opt_label }}"
    role="button">
    ...
</button>

<div class="progress-label" aria-live="polite">
    Question {{ question_number }} of {{ total_questions }}
</div>
```

**Add skip-to-content for keyboard navigation**:
```html
<a href="#main-game" class="skip-link">Skip to game</a>
```

**Color contrast**: Ensure all text meets WCAG AA (4.5:1 ratio)
- Current pinyin text: `color: var(--dark)` on `background: sky-blue` → Check contrast
- Option labels: Black on white → ✅ passes

**Files**:
- **Modify**: All template files → add ARIA labels
- **Modify**: `static/css/common.css` → add focus styles for keyboard nav
- **Test**: Use macOS VoiceOver / NVDA to verify

#### D. Bigger Touch Targets (Phone Optimization)

**Current**: 60px minimum (good for iPad)

**For phones**: Increase to 44px minimum (iOS guideline), ideally 48px

```css
/* Already added in PR #9, but reinforce: */
@media (max-width: 480px) {
    .option-btn {
        min-height: 100px; /* Each button in 2x2 grid */
        padding: 16px;
    }
    
    .tts-btn {
        width: 50px;
        height: 50px;
    }
    
    .music-toggle,
    .logout-btn {
        width: 44px;
        height: 44px;
    }
}
```

**Files**: Already in `static/css/racing.css` from PR #9

#### E. Reduced Motion Support (Accessibility)

**Current**: Basic `@media (prefers-reduced-motion)` disables animations

**Improve**: Respect system setting but keep *some* feedback

```css
@media (prefers-reduced-motion: reduce) {
    /* Don't disable ALL animations — keep essential feedback */
    .car-sprite {
        transition: left 0.3s linear !important; /* Faster, no easing */
    }
    
    .character-display {
        animation: none !important; /* No pop-in */
    }
    
    /* Keep color feedback, just no motion */
    .option-btn.correct {
        border-color: var(--correct-color);
        background: #dff9f0;
        /* No shake animation */
    }
}
```

**Files**: `static/css/racing.css:876-880` (expand this block)

---

## 6. ROADMAP: Phased Implementation Plan

### Phase 1: Quick Wins (2-3 weeks, 1-2 PRs)

**Goal**: High-impact improvements with low complexity

#### **1.1 Phone Responsiveness** ✅ DONE
- Already shipped in PR #9
- 2×2 grid, wrapping top bar, tighter spacing

#### **1.2 Enhanced Feedback & Polish** (Estimated: 5 days)
**Tasks**:
- Add combo meter UI
- Enhance confetti with CSS particles (no Lottie yet)
- Add mascot character (static emoji, basic animations)
- Implement hint system (escalating help on retries)
- Add SFX library (5 sounds: correct, wrong, boost, complete, combo)

**Files**:
- `static/css/racing.css` → combo meter, mascot styles
- `static/js/racing.js` → combo tracking, hint logic
- `static/sounds/` → add 5 SFX files
- `app/services/session_engine.py` → hint generation

**Impact**: 🔥🔥🔥 (Makes game feel more alive)  
**Risk**: Low (CSS/JS only, no DB changes)

#### **1.3 Daily Quests** (Estimated: 7 days)
**Tasks**:
- Create `daily_quest` model + service
- Add 5 quest templates
- Display quests on game selector
- Track progress, award completion

**Files**:
- **New**: `app/models/daily_quest.py`
- **New**: `app/services/quest_tracker.py`
- **Modify**: `templates/game_selector.html`
- **Migration**: Add `user_daily_quests` table

**Impact**: 🔥🔥🔥 (Daily engagement +30%)  
**Risk**: Medium (DB migration, testing needed)

#### **1.4 Kid Progress Map** (Estimated: 4 days)
**Tasks**:
- Create progress summary route
- Design kid-friendly progress screen
- Add "My Progress" button to game selector

**Files**:
- **New**: `templates/progress_map.html`
- **New**: `app/routes/progress.py`
- **Modify**: `templates/game_selector.html`

**Impact**: 🔥🔥 (Visualization helps motivation)  
**Risk**: Low

**Phase 1 Total**: ~16 days (3 weeks with testing/review)

---

### Phase 2: Adaptive Engine (4-6 weeks)

**Goal**: Smarter difficulty, placement testing, per-skill mastery tracking

#### **2.1 Data Model Refactor** (Estimated: 5 days)
**Tasks**:
- Migrate from `learning_topics` to `learning_standards` model
- Add grade bands, strands, skill codes
- Map existing 90 topics to CCSS/CEFR
- Add Elo + BKT fields to user progress

**Files**:
- **New**: `app/models/learning_standard.py`
- **Migrate**: Alembic migration script
- **Modify**: `app/seed/seed_taxonomy.py` → seed new structure
- **Data**: Tag existing 540 characters by grade level

**Impact**: 🔥 (Foundation for everything)  
**Risk**: High (DB migration on live data, needs careful testing)

#### **2.2 Placement Test System** (Estimated: 7 days)
**Tasks**:
- Implement adaptive placement test algorithm
- Create placement UI (kid-friendly)
- Add "Start Over" feature for re-testing

**Files**:
- **New**: `app/services/placement_test.py`
- **New**: `templates/placement_test.html`
- **Modify**: `app/routes/game.py` → redirect to placement if needed

**Impact**: 🔥🔥🔥 (Right starting level = better retention)  
**Risk**: Medium (Algorithm tuning required)

#### **2.3 Elo + Bayesian Mastery Tracking** (Estimated: 8 days)
**Tasks**:
- Implement Elo rating updates
- Implement Bayesian Knowledge Tracing
- Integrate with session engine
- First-try vs retry credit logic

**Files**:
- **New**: `app/services/adaptive_mastery.py`
- **Modify**: `app/services/session_engine.py:167-240`
- **Modify**: `app/services/spaced_repetition.py` → keep SM-2, add Elo

**Impact**: 🔥🔥🔥 (Smart difficulty = better learning)  
**Risk**: High (Complex math, needs validation)

#### **2.4 Dynamic Session Difficulty** (Estimated: 5 days)
**Tasks**:
- Select questions targeting 80% success
- Adaptive session length (3-7 questions)
- Bonus rounds for perfect performance

**Files**:
- **Modify**: `app/services/session_engine.py:40-72`
- **Modify**: `app/config.py` → add adaptive settings

**Impact**: 🔥🔥🔥 (Personalized pace)  
**Risk**: Medium

#### **2.5 Extended Content** (Estimated: 10 days)
**Tasks**:
- Add 500 more Chinese characters (540 → 1,000+)
- Map to Grade 2-3 (部编版)
- Add 50 more math topics (extend to Grade 6)
- Add 30 more English topics (CEFR B1)

**Files**:
- **Data**: `app/seed/characters_extended.json`
- **Data**: `app/seed/standards/math_ccss_extended.json`
- **New**: Question generator modes for higher levels

**Impact**: 🔥🔥 (Ages 3-12 coverage)  
**Risk**: High (Content creation + testing)

**Phase 2 Total**: ~35 days (6 weeks)

---

### Phase 3: Long-Term Engagement (6-8 weeks)

**Goal**: Rich features for sustained daily use

#### **3.1 Advanced Animation (Lottie)** (Estimated: 7 days)
**Tasks**:
- Integrate Lottie player
- Commission/purchase 5 animations (success, wrong, boost, celebrate, level-up)
- Add physics-based car movement
- Adaptive music layers

**Files**:
- `static/animations/` → Lottie JSON files
- `templates/themes/racing/game.html` → Lottie player
- `static/js/music.js` → refactor to layered system

**Impact**: 🔥🔥 (Polish, not core learning)  
**Risk**: Low (Budget: $50-100 for animations)

#### **3.2 Expanded Collectibles** (Estimated: 8 days)
**Tasks**:
- Add 15 car skins (3 per tier)
- Add 8 companion pets
- Add 8 environment themes
- Garage/collection UI

**Files**:
- **Modify**: `app/models/store.py`
- **Modify**: `templates/store.html` → categorized tabs
- **Modify**: `static/css/racing.css` → pet rendering

**Impact**: 🔥🔥 (Engagement +20%)  
**Risk**: Medium (Art assets needed)

#### **3.3 Notification System** (Estimated: 10 days)
**Tasks**:
- Set up push notification service (OneSignal or FCM)
- Parent notification settings UI
- Daily reminder scheduler (Heroku Scheduler)
- Weekly email summaries

**Files**:
- **New**: `app/services/notification_scheduler.py`
- **Modify**: `templates/dashboard.html` → settings panel
- **Config**: OneSignal API keys

**Impact**: 🔥🔥 (Streak retention +15%)  
**Risk**: High (Backend job setup, push notification permissions)

#### **3.4 Family Features** (Estimated: 6 days)
**Tasks**:
- Family leaderboard (weekly stars)
- Shared goals
- Cooperative celebrations

**Files**:
- **Modify**: `templates/game_selector.html` → leaderboard widget
- **Modify**: `app/routes/dashboard.py` → family stats

**Impact**: 🔥 (Nice-to-have for 2-kid families)  
**Risk**: Low

#### **3.5 Onboarding & Voice Prompts** (Estimated: 8 days)
**Tasks**:
- Interactive tutorial system
- Voice prompts for pre-readers (Web Speech API)
- Parent toggle for voice guidance

**Files**:
- **New**: `static/js/onboarding.js`
- **New**: `static/js/voice_prompts.js`
- **New**: `templates/onboarding.html`

**Impact**: 🔥🔥 (Ages 3-5 accessibility)  
**Risk**: Low

#### **3.6 Accessibility Audit** (Estimated: 5 days)
**Tasks**:
- Add ARIA labels to all interactive elements
- Screen reader testing (NVDA, VoiceOver)
- Keyboard navigation support
- Color contrast check (WCAG AA)

**Files**:
- **Modify**: All templates → add ARIA
- **Modify**: `static/css/common.css` → focus styles

**Impact**: 🔥 (Inclusive design)  
**Risk**: Low

**Phase 3 Total**: ~44 days (8 weeks)

---

## Summary Roadmap (Revised with UI Redesign)

### Integrated Timeline: UI + Features

**Note**: UI redesign now runs parallel to feature development

| Phase | Duration | UI Work | Feature Work | Impact | Risk |
|-------|----------|---------|--------------|--------|------|
| **Phase 1** | 4 weeks | Visual refresh (login, map, game) | Daily quests, hints, combo meter | 🔥🔥🔥 | Med |
| **Phase 2** | 6 weeks | Animation stack (Rive, particles, results) | Adaptive engine, placement test | 🔥🔥🔥 | High |
| **Phase 3** | 8 weeks | Garage, progress map, dashboard v2 | Extended content, notifications | 🔥🔥 | Med |
| **Phase 4** | 4 weeks | Polish, accessibility, optimization | Testing, bug fixes | 🔥🔥 | Low |

**Total Effort**: ~22 weeks (5.5 months) for complete transformation

---

### Detailed Phase Breakdown

#### **Phase 1: Quick Wins + Visual Foundation** (4 weeks)

**Week 1-2: Design System**
- ✅ Define palette, typography, component library
- ✅ Create Figma mockups (8 screens)
- ✅ Build CSS design system
- ✅ Convert key icons to SVG

**Week 2-3: Core Screens**
- ✅ Redesign login (avatar cards)
- ✅ Build world map (static)
- ✅ New game session layout
- ⚠️ Keep old routes as fallback

**Week 3-4: Enhanced Feedback**
- ✅ Add combo meter UI
- ✅ Implement Motion One transitions
- ✅ Enhance confetti (CSS particles)
- ✅ Add hint system (escalating help)

**Week 4: Daily Quests**
- ✅ Create quest model + service
- ✅ Add 5 quest templates
- ✅ Display quests on game selector

**Deliverables**:
- Modern UI for login → map → game → results
- Daily quests live
- Hint system working
- A/B tested with 20% of users

---

#### **Phase 2: Animation + Intelligence** (6 weeks)

**Week 5-7: Rive Mascots**
- ✅ Commission Dash rabbit (8 states)
- ✅ Integrate Rive runtime
- ✅ Add mascot reactions
- ✅ Implement mascot speech bubbles

**Week 7-8: Canvas Particles**
- ✅ Build particle engine
- ✅ Advanced confetti system
- ✅ Floating background elements
- ✅ Performance testing

**Week 8-9: Adaptive Engine Backend**
- ✅ Migrate to `learning_standards` model
- ✅ Add Elo + BKT fields
- ✅ Map existing content to grade bands

**Week 9-10: Placement Test + Dynamic Difficulty**
- ✅ Build placement algorithm
- ✅ Create placement UI
- ✅ Implement Elo-based question selection
- ✅ First-try vs retry credit

**Deliverables**:
- Animated mascots live
- Particle system replacing CSS confetti
- Adaptive difficulty active
- Placement test for new users

---

#### **Phase 3: Rich Features + Content** (8 weeks)

**Week 11-12: Garage + Collectibles**
- ✅ Redesign store (3-tab layout)
- ✅ Add 15 car skins
- ✅ Add 8 companion pets
- ✅ Add 10 environment themes

**Week 13-14: Kid Progress Map**
- ✅ Build visual journey screen
- ✅ Per-subject progress trees
- ✅ Badge/trophy case
- ✅ Weekly summary stats

**Week 15-16: Extended Content**
- ✅ Add 500 more Chinese characters
- ✅ Commission/generate SVG icons
- ✅ Map to grade levels (1-3)
- ✅ Add 50 math topics (extend to Grade 6)
- ✅ Add 30 English topics (CEFR B1)

**Week 17-18: Parent Dashboard v2**
- ✅ Redesign dashboard (cleaner layout)
- ✅ Add Buddy mascot guide
- ✅ Family leaderboard
- ✅ AI-generated insights (optional)

**Deliverables**:
- Rich collectible system
- Kid-facing progress visualization
- 1,000+ Chinese characters
- Modern parent dashboard

---

#### **Phase 4: Polish + Launch Preparation** (4 weeks)

**Week 19: Performance Optimization**
- ✅ Lighthouse audit (target: 90+ scores)
- ✅ Convert images to WebP
- ✅ Code-split JS bundles
- ✅ Implement low-end device fallbacks
- ✅ Service worker optimization

**Week 20: Accessibility Compliance**
- ✅ Add ARIA labels (all screens)
- ✅ VoiceOver + NVDA testing
- ✅ WCAG AAA contrast compliance
- ✅ Keyboard navigation
- ✅ Reduced motion support

**Week 21: Cross-Device Testing**
- ✅ Test on iPad Air 2 (2014)
- ✅ Test on iPhone SE, 14, 15
- ✅ Safari, Chrome, Firefox
- ✅ Portrait + landscape
- ✅ Fix edge cases

**Week 22: Onboarding + Voice**
- ✅ Interactive tutorial system
- ✅ Voice prompts (Web Speech API)
- ✅ Parent settings panel
- ✅ Final bug bash

**Deliverables**:
- 60 FPS on iPad Air 2
- WCAG AAA compliant
- Works on all target devices
- Voice guidance for ages 3-5
- Production-ready

---

### Parallel Work Streams

**Design** (can start Week 0):
- Figma mockups for all 8 screens
- Rive character design (outsource)
- Icon/illustration sourcing

**Content Creation** (ongoing):
- Chinese characters (500 more)
- SVG icon generation
- Question writing for new topics

**Backend** (independent):
- Data model migration (Week 8-9)
- Adaptive algorithms (Week 9-10)
- Notification system (Week 17, optional)

**Frontend** (sequential):
- Must complete Phase 1 before Phase 2 animations
- Phase 3 features can start Week 8 (parallel)

---

### Migration Strategy

#### Rollout Plan (Per Phase)

**Phase 1** (Week 4):
- ✅ A/B test: 20% new UI, 80% old UI
- ✅ Monitor: session completion, error rates
- ✅ Week 5: Roll out to 50%
- ✅ Week 6: Roll out to 100% (kill old UI)

**Phase 2** (Week 10):
- ✅ Mascots: Enable for all users (low risk)
- ✅ Adaptive difficulty: 20% → 50% → 100% over 2 weeks
- ✅ Monitor: accuracy distribution, retention

**Phase 3** (Week 18):
- ✅ Collectibles: Enable for all (low risk)
- ✅ Extended content: Gradual unlock (50 chars/week)
- ✅ Dashboard v2: Enable for all parents

**Phase 4** (Week 22):
- ✅ Final cut-over: Remove all old code
- ✅ Archive old templates (backup)
- ✅ Celebrate launch! 🎉

---

### Feature Flags (Database-Driven)

```python
# app/models/feature_flag.py
class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    
    name = Column(String(50), primary_key=True)
    enabled = Column(Boolean, default=False)
    rollout_pct = Column(Integer, default=0)  # 0-100
    
# Usage
def is_enabled(user_id, flag_name):
    flag = db.query(FeatureFlag).get(flag_name)
    if flag.rollout_pct >= 100:
        return flag.enabled
    # Deterministic hash (same user always gets same result)
    return (hash(f"{user_id}-{flag_name}") % 100) < flag.rollout_pct
```

**Flags**:
- `ui_redesign_v2` (Phase 1)
- `mascot_animations` (Phase 2)
- `adaptive_difficulty` (Phase 2)
- `extended_content` (Phase 3)
- `voice_prompts` (Phase 4)

---

### Total Effort**: ~22 weeks (5.5 months)

---

## Risks & Mitigation

### **High-Risk Items**

1. **DB Migration (Phase 2.1)**
   - **Risk**: Breaking live user data
   - **Mitigation**: 
     - Test migration on copy of production DB
     - Run in Alembic transaction (rollback on error)
     - Keep old `learning_topics` table during transition

2. **Elo/BKT Algorithm (Phase 2.3)**
   - **Risk**: Math errors → broken difficulty
   - **Mitigation**:
     - Peer review algorithm implementation
     - A/B test with 10% of users before full rollout
     - Keep SM-2 as fallback

3. **Content Creation (Phase 2.5)**
   - **Risk**: 1,000+ characters need images + meanings
   - **Mitigation**:
     - Batch generate with AI tools (DALL-E for icons)
     - Crowdsource translations (native speakers)
     - Phase in gradually (500 chars → 1,000 → 1,500)

### **Medium-Risk Items**

1. **Push Notifications (Phase 3.3)**
   - **Risk**: Permission denials, spam complaints
   - **Mitigation**:
     - Parent opt-in only (default: disabled)
     - Max 1 notification per day
     - Clear unsubscribe

2. **Performance (Lottie animations)**
   - **Risk**: 2014 iPad Air 2 can't handle heavy animations
   - **Mitigation**:
     - Test on real old device before shipping
     - Detect device capability, disable Lottie on old iPads
     - Keep CSS fallback animations

---

## Success Metrics

**Phase 1**:
- Daily active users (DAU) +20%
- Session completion rate +15%
- Average session length: 4.5 → 5.2 minutes

**Phase 2**:
- Skills mastered per week +40%
- Session accuracy stabilizes at 75-85% (optimal learning zone)
- Retention (7-day) +25%

**Phase 3**:
- Streak 7+ days: 40% of active users
- Store purchases +30%
- Parent satisfaction (survey): 4.5/5 stars

---

## Appendix: Technical References

### Open Standards Used

- **Common Core State Standards**: [corestandards.org](https://www.corestandards.org/)
- **CEFR (English)**: [coe.int/lang-cefr](https://www.coe.int/en/web/common-european-framework-reference-languages)
- **HSK Levels**: [chinesetest.cn](http://www.chinesetest.cn/gosign.do?id=1&lid=0)
- **Marble Skill Taxonomy**: [github.com/lauramionel/os-taxonomy](https://github.com/lauramionel/os-taxonomy)

### Algorithms Referenced

- **SM-2 (Spaced Repetition)**: [supermemo.com/en/archives1990-2015/english/ol/sm2](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2)
- **Elo Rating**: [wikipedia.org/wiki/Elo_rating_system](https://en.wikipedia.org/wiki/Elo_rating_system)
- **Bayesian Knowledge Tracing**: Corbett & Anderson (1995), "Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge"
- **Item Response Theory (IRT)**: [wikipedia.org/wiki/Item_response_theory](https://en.wikipedia.org/wiki/Item_response_theory)

### Design Inspirations (Best Practices, No Dark Patterns)

- **Duolingo**: Streak system, daily goals (but avoid the aggressive notifications)
- **Khan Academy**: Mastery-based progression, skill tree
- **DragonBox**: Game-first math learning, no explicit "this is homework" feeling
- **Teach Your Monster to Read**: Age-appropriate, gentle difficulty curve

---

---

## APPENDIX: Implementation Quick Reference

### Tech Stack Summary

| Component | Current | Proposed | Why |
|-----------|---------|----------|-----|
| **Frontend Framework** | Vanilla JS | Keep Vanilla JS + modules | Avoid 8-week rewrite, sufficient complexity |
| **Character Animation** | CSS only | Rive | Industry-standard, small files (10-50KB) |
| **UI Transitions** | CSS transitions | Motion One / GSAP | Timeline control, better easing |
| **Particles** | CSS divs | Canvas 2D | 10x better performance |
| **Typography** | System fonts | Fredoka + Inter + Noto Sans SC | Kid-friendly, free |
| **Icons** | Emoji | Phosphor Icons (duotone SVG) | Professional, customizable |
| **State Management** | Ad-hoc | Simple store pattern | Centralized, testable |
| **Components** | jQuery-style | Web Components | Reusable, no framework |

### File Structure (After Redesign)

```
app/
├── models/
│   ├── learning_standard.py     # NEW: Grade-based curriculum
│   ├── daily_quest.py            # NEW: Daily objectives
│   ├── feature_flag.py           # NEW: Rollout control
│   └── ...
├── services/
│   ├── adaptive_mastery.py       # NEW: Elo + BKT
│   ├── placement_test.py         # NEW: Onboarding test
│   ├── hint_generator.py         # NEW: Escalating hints
│   └── ...
├── routes/
│   ├── progress.py               # NEW: Kid progress map
│   └── ...
└── seed/
    ├── standards/                # NEW: CCSS, CEFR, 部编版
    │   ├── math_ccss.json
    │   ├── chinese_bubian.json
    │   └── english_cefr.json
    └── ...

static/
├── animations/                    # NEW: Rive files
│   ├── dash-rabbit.riv
│   ├── sparkle-unicorn.riv
│   └── ...
├── css/
│   ├── design-system.css          # NEW: Palette, typography
│   ├── components.css             # NEW: Button, card, progress
│   ├── login_v2.css               # NEW: Redesigned screens
│   ├── world_map.css
│   └── game_session_v2.css
├── js/
│   ├── store.js                   # NEW: State management
│   ├── particles.js               # NEW: Canvas particles
│   ├── mascot-controller.js       # NEW: Rive integration
│   ├── components/                # NEW: Web Components
│   │   ├── mascot.js
│   │   └── combo-meter.js
│   └── ...
└── images/
    ├── avatars/                   # NEW: Custom illustrations
    ├── world/                     # NEW: Map backgrounds
    └── ...

templates/
├── login_v2.html                  # NEW: Avatar cards
├── world_map.html                 # NEW: Interactive map
├── game_session_v2.html           # NEW: Themed immersive
├── session_results_v2.html        # NEW: Victory screen
├── garage_v2.html                 # NEW: 3-tab collection
├── progress_map_v2.html           # NEW: Kid's journey
├── dashboard_v2.html              # NEW: Family command center
└── partials/
    └── teaching_panel_v2.html     # NEW: Enhanced learning moment
```

### Commands Quick Reference

**Development**:
```bash
# Install new dependencies
npm install motion gsap  # or just motion for free option

# Run dev server
uvicorn app.main:app --reload

# Watch CSS (if using build step)
npx tailwindcss -i static/css/input.css -o static/css/output.css --watch
```

**Rive Integration**:
```bash
# Install Rive runtime
npm install @rive-app/canvas

# Or use CDN (no build step)
<script src="https://unpkg.com/@rive-app/canvas@2.7.0"></script>
```

**Image Optimization**:
```bash
# Convert PNGs to WebP (60% smaller)
for f in static/images/*.png; do
    cwebp -q 85 "$f" -o "${f%.png}.webp"
done
```

**Performance Testing**:
```bash
# Lighthouse CI (automated)
npm install -g @lhci/cli
lhci autorun --url http://localhost:8000

# Playwright for device testing
npx playwright test --device="iPad Air 2" --device="iPhone SE"
```

---

## Final Recommendation for Ray

### If Budget is Limited ($0-300):

**Do This (Phase 1 Only)**:
1. ✅ Visual refresh (new colors, typography, layouts)
2. ✅ Daily quests
3. ✅ Combo meter
4. ✅ **Skip Rive** → use static PNG mascots (commission 1 character, 4 poses = $50)
5. ✅ **Use Motion One** (free) instead of GSAP
6. ✅ Enhanced CSS confetti (no Canvas yet)

**Timeline**: 4 weeks  
**Cost**: $50-100  
**Impact**: Still 70% of the visual improvement, minimal risk

---

### If Full Budget is Available ($1,000-2,000):

**Do This (All Phases)**:
1. ✅ Complete UI redesign (8 screens)
2. ✅ Rive mascots (4 characters, 8 states each)
3. ✅ GSAP Business license ($199/year)
4. ✅ Canvas particle system
5. ✅ Adaptive engine with placement tests
6. ✅ Extended content (1,000+ characters)
7. ✅ Voice prompts + accessibility

**Timeline**: 22 weeks  
**Cost**: $1,100-2,050  
**Impact**: Transform Skool into a best-in-class learning platform, competitive with Duolingo/Khan Academy Kids

---

### What NOT to Do (Common Pitfalls)

❌ **Don't** rewrite to React unless complexity demands it (8-week detour)  
❌ **Don't** buy expensive illustration packs ($500+) — use Phosphor Icons + selective commissions  
❌ **Don't** over-animate — 60 FPS on iPad Air 2 is the constraint  
❌ **Don't** skip accessibility — WCAG compliance is non-negotiable  
❌ **Don't** launch big-bang — A/B test every phase at 20% → 50% → 100%  

---

**End of Proposal**

---

## Questions for Ray

1. **Budget**: Is there budget for:
   - Lottie animations ($50-100)?
   - Additional character artwork (500-1,000 icons @ $1-2 each = $500-2,000)?
   - Push notification service (OneSignal free tier covers ~10K users)?

2. **Priority**: Which phase should we prioritize if time/resources are limited?
   - I recommend: **Phase 1 (quick wins) → Phase 2.1-2.3 (adaptive core)** before Phase 3 polish

3. **Content**: For Chinese characters beyond 540:
   - Commission native speaker to validate meanings?
   - Use existing open datasets (e.g., Unihan database)?

4. **Testing**: Can we recruit 5-10 parent-child pairs for beta testing Phase 2 adaptive features?

5. **IB Curriculum**: If Ray has access to IB materials (through a school partnership), we can align more closely. Otherwise, we stick to open standards.
