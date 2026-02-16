This is a wonderful project! Let me think through this carefully before you jump into implementation with Claude Code, because good planning here will save you a lot of rework later.

## Key Design Thoughts

**The two-player problem is actually a multi-player platform problem.** Since your daughter might share this with friends, you're really building a lightweight learning platform, not just a family app. That changes some architectural decisions.

**Separate themes, shared engine.** Your daughter and son need very different experiences visually, but the core mechanics (present challenge → check answer → give feedback → award points) are the same. I'd suggest building one game engine with swappable "theme packs."

## Architecture Recommendations

**For hosting on Heroku with the possibility of other users, I'd suggest a simpler stack than Java:**

A React frontend with a Node.js/Express backend and PostgreSQL would be lighter, cheaper on Heroku, and faster to iterate on. Java is fine but might be overkill for this stage, and Heroku's free/cheap tiers work better with Node. That said, if you're more comfortable with Java + Spring Boot, it'll work too — just heavier to deploy and maintain.

**Data model to think about:**

The core entities would be users (with profile info like name, age, theme preference), a character bank (characters with pinyin, meaning, difficulty level, and optional tags), a session log (tracking which user played when, what questions were asked, and whether answers were correct), and a points ledger (recording points earned per session, running total, and redemption history if you add that later).

**The progressive difficulty system** is where the real learning value lives. I'd suggest a simple spaced-repetition-lite approach: characters they get wrong come back sooner, characters they get right get spaced out further. Track a "mastery score" per character per user. New characters get introduced when they've shown they know the current batch. This turns it from a quiz into an actual learning tool.

## Feature Priorities for V1

I'd recommend building in phases.

**Phase 1 — Playable MVP:** Simple login (username + parent-set PIN, no passwords for kids), one game mode with multiple-choice character recognition (show a character, pick the correct meaning from four options), five questions per session, points awarded on completion, and two themes — a pony/pastel theme for your daughter and a racing/car theme for your son.

**Phase 2 — Smart Learning:** Spaced repetition so missed characters return more frequently, difficulty progression (single characters → two-character words → short phrases), and a parent dashboard so you can see their progress and add custom content from school curriculum.

**Phase 3 — Engagement Extras:** Car logo recognition mode for your son, daily streaks and bonus points, the ability for friends to create accounts, and possibly a simple leaderboard among friends.

## A Few Specific Suggestions

**For your son (age 4):** Multiple choice with images will work much better than typing. For the racing theme, think of it as a road with stops — at each stop a character appears, he taps the right answer, and the car zooms to the next stop. Five stops = one race = one session. Start with very basic characters like 大, 小, 车, 人, 口.

**For your daughter (grade 3):** She can handle more complexity. Mix in contextual sentences — show a sentence with a blank and have her pick the right character to complete it. This maps well to school curriculum. For the My Little Pony theme, you could frame each session as helping a pony complete a quest.

**For the curriculum integration you mentioned:** Build an admin/parent interface where you can paste in characters or word lists. Tag them by difficulty and topic. This way when her teacher sends home a character list, you just add them and they show up in her next session.

**For the points system:** Keep it visible and satisfying. Show points animating upward after each correct answer. Show a running weekly total. Maybe even a simple "piggy bank" visualization that fills up. The connection to real money (5 points = 5 RMB) is great motivation — you don't need to automate redemption, just make the point total clear so you can settle up weekly.

## Before You Start in Claude Code

I'd recommend preparing a few things. First, a character list for each difficulty level — even 20-30 characters per level is enough to start. Second, decide on your stack (I'd recommend React + Node + PostgreSQL, but confirm what you're comfortable with). Third, sketch the two themes roughly — even just color palettes and the general vibe. Fourth, decide on your Heroku setup — will you use Heroku Postgres? One app or separate frontend/backend?

Want me to draft a more detailed technical spec or data schema that you could hand directly to Claude Code? Or would you prefer I build a working prototype right now as an HTML artifact so you can see the gameplay feel before committing to the full architecture?