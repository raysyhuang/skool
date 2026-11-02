import json
import random
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import GameSession, SessionQuestion
from app.models.rewards import PointsLedger
from app.services.question_generator import select_characters, generate_question, pick_question_mode
from app.services.spaced_repetition import update_mastery, update_topic_mastery
from app.services.rewards import award_points
from app.services.math_generator import generate_math_questions, generate_math_question
from app.services.logic_generator import generate_logic_questions
from app.services.english_generator import generate_english_questions, generate_english_question
from app.services.topic_selection import select_topics, drill_topics
from app.config import get_settings


class SessionLimitReached(Exception):
    pass


def _has_daily_bonus_award(db: Session, user_id: int, target_day: date) -> bool:
    entries = (
        db.query(PointsLedger)
        .filter_by(user_id=user_id, reason="daily_bonus")
        .all()
    )
    return any(e.created_at and e.created_at.date() == target_day for e in entries)


def can_start_session(user: User) -> bool:
    """Check if user can start a new session today. 0 = unlimited."""
    user.reset_daily_if_needed()
    limit = get_settings().max_sessions_per_day
    if limit <= 0:
        return True
    return user.sessions_today < limit


def create_session(db: Session, user: User, game_type: str = "chinese",
                   character_ids: list[int] | None = None,
                   topic_ids: list[int] | None = None) -> GameSession:
    """Create a new game session with 5 questions."""
    user.reset_daily_if_needed()
    settings = get_settings()

    if settings.max_sessions_per_day > 0 and user.sessions_today >= settings.max_sessions_per_day:
        raise SessionLimitReached("Daily session limit reached. Come back tomorrow!")

    game_session = GameSession(user_id=user.id, game_type=game_type)
    db.add(game_session)
    db.flush()

    if game_type == "chinese":
        _create_chinese_questions(db, game_session, user, settings, character_ids=character_ids)
    elif game_type == "math":
        _create_math_questions(db, game_session, user, settings, topic_ids=topic_ids)
    elif game_type == "logic":
        _create_logic_questions(db, game_session, user, settings)
    elif game_type == "english":
        _create_english_questions(db, game_session, user, settings, topic_ids=topic_ids)
    else:
        raise ValueError(f"Unknown game type: {game_type}")

    # Update user session count
    user.record_play_today()
    user.sessions_today += 1

    db.commit()
    return game_session


def _create_chinese_questions(db: Session, game_session: GameSession, user: User, settings, character_ids: list[int] | None = None) -> None:
    """Create Chinese character questions (original logic)."""
    is_prereader = (user.age or 5) <= 5
    characters = select_characters(db, user.id, count=settings.questions_per_session, is_prereader=is_prereader, character_ids=character_ids)

    if not characters:
        raise ValueError("No characters available for this user.")

    for i, char in enumerate(characters, 1):
        mode = pick_question_mode(is_prereader, char)
        q_data = generate_question(db, char, mode, count=settings.distractors_per_question)

        question = SessionQuestion(
            session_id=game_session.id,
            character_id=char.id,
            question_number=i,
            correct_answer=q_data["correct_answer"],
            options=json.dumps(q_data["options"]),
            question_mode=mode,
        )
        db.add(question)


def _create_math_questions(db: Session, game_session: GameSession, user: User, settings,
                           topic_ids: list[int] | None = None) -> None:
    """Create math questions, driven by the taxonomy topic spine where possible."""
    count = settings.questions_per_session
    topics = drill_topics(db, topic_ids, count) or select_topics(db, user, "math", count)

    if topics:
        for i, topic in enumerate(topics, 1):
            mq = generate_math_question(topic.question_mode)
            db.add(_topic_question(game_session, i, mq, topic.id))
        return

    # No topics seeded (fresh DB, or the taxonomy import was skipped) — keep the
    # original age-bucketed random rotation working.
    age = user.age or 5
    for i, mq in enumerate(generate_math_questions(age, count=count), 1):
        db.add(_topic_question(game_session, i, mq, None))


def _create_logic_questions(db: Session, game_session: GameSession, user: User, settings) -> None:
    """Create logic questions based on user age."""
    age = user.age or 5
    logic_qs = generate_logic_questions(age, count=settings.questions_per_session)

    for i, lq in enumerate(logic_qs, 1):
        question = SessionQuestion(
            session_id=game_session.id,
            character_id=None,
            question_number=i,
            correct_answer=lq["correct_answer"],
            options=json.dumps(lq["options"]),
            question_mode=lq["mode"],
            prompt_data=lq["prompt_data"],
        )
        db.add(question)


def _create_english_questions(db: Session, game_session: GameSession, user: User, settings,
                              topic_ids: list[int] | None = None) -> None:
    """Create English questions, driven by the taxonomy topic spine where possible."""
    count = settings.questions_per_session
    age = user.age or 5
    topics = drill_topics(db, topic_ids, count) or select_topics(db, user, "english", count)

    if topics:
        for i, topic in enumerate(topics, 1):
            eq = generate_english_question(topic.question_mode, age)
            db.add(_topic_question(game_session, i, eq, topic.id))
        return

    for i, eq in enumerate(generate_english_questions(age, count=count), 1):
        db.add(_topic_question(game_session, i, eq, None))


def _topic_question(
    game_session: GameSession, number: int, q: dict, topic_id: int | None
) -> SessionQuestion:
    """Build a SessionQuestion from a generator payload."""
    return SessionQuestion(
        session_id=game_session.id,
        character_id=None,
        topic_id=topic_id,
        question_number=number,
        correct_answer=q["correct_answer"],
        options=json.dumps(q["options"]),
        question_mode=q["mode"],
        prompt_data=q["prompt_data"],
    )


def _lock_for_scoring(db: Session, user: User, *session_filters) -> GameSession | None:
    """Row-lock the user and the session before checking-then-awarding points.

    Two gunicorn workers can otherwise both pass "not answered yet" /
    "not completed yet" and award the same points twice. Locks are taken
    user-first so concurrent requests can't deadlock (SQLite ignores them).
    """
    db.query(User).filter_by(id=user.id).with_for_update().populate_existing().one()
    return (
        db.query(GameSession).filter(*session_filters)
        .with_for_update().populate_existing().first()
    )


def submit_answer(db: Session, user: User, question_id: int, selected_answer: str) -> dict:
    """Submit an answer for a question. Returns result dict."""
    question = db.query(SessionQuestion).filter_by(id=question_id).first()
    if not question:
        raise ValueError("Question not found")

    session = _lock_for_scoring(db, user, GameSession.id == question.session_id)
    if session is None:
        raise ValueError("Question not found")
    db.refresh(question)  # re-read under the lock: a concurrent tap may have answered it
    if session.user_id != user.id:
        raise ValueError("This question doesn't belong to you")
    if session.completed_at:
        raise ValueError("Session already completed")

    was_answered = question.selected_answer is not None
    was_correct = bool(question.is_correct)
    if was_answered and was_correct:
        raise ValueError("Question already answered correctly")

    settings = get_settings()
    is_correct = selected_answer == question.correct_answer
    points = settings.points_wrong
    bonus_text = None

    question.selected_answer = selected_answer
    question.answered_at = datetime.now(timezone.utc)

    if not was_answered:
        question.is_correct = is_correct

        # Combo tracking
        if is_correct:
            session.current_combo = (session.current_combo or 0) + 1
            if session.current_combo > (session.max_combo or 0):
                session.max_combo = session.current_combo
            
            # Combo bonus (every 3 correct)
            if session.current_combo >= 3 and session.current_combo % 3 == 0:
                combo_points = 2 * (session.current_combo // 3)
                session.combo_bonus = (session.combo_bonus or 0) + combo_points
                session.points_earned += combo_points
                award_points(db, user, combo_points, f"combo_x{session.current_combo}")
                bonus_text = f"combo_x{session.current_combo}"
        else:
            session.current_combo = 0

        # Update mastery on first answer attempt (SM-2 with quality)
        # Reduced quality if hint was used
        first_try = question.first_try if question.first_try is not None else True
        if question.character_id is not None:
            update_mastery(db, user.id, question.character_id, is_correct, is_first_attempt=first_try)
        if question.topic_id is not None:
            update_topic_mastery(db, user.id, question.topic_id, is_correct, is_first_attempt=first_try)

        if is_correct:
            points = settings.points_correct

            # Lucky star: random chance of multiplied points
            if random.random() < settings.lucky_star_chance:
                points *= settings.lucky_star_multiplier
                if not bonus_text:
                    bonus_text = "lucky_star"

            # Speed bonus: answered within threshold
            if question.started_at and question.answered_at:
                # Ensure both datetimes are naive for subtraction
                # (PostgreSQL may return naive timestamps even when stored with tz)
                a = question.answered_at.replace(tzinfo=None)
                s = question.started_at.replace(tzinfo=None)
                delta = (a - s).total_seconds()
                if delta <= settings.speed_bonus_threshold_seconds:
                    points += 1
                    if not bonus_text:
                        bonus_text = "speed_bonus"

            session.total_correct += 1
            session.points_earned += points
            award_points(db, user, points, "correct_answer")
        else:
            session.total_wrong += 1
    else:
        # Retry path: only state transition from wrong -> correct changes score.
        if is_correct:
            question.is_correct = True
            points = settings.points_correct
            session.total_correct += 1
            if question.character_id is not None:
                update_mastery(db, user.id, question.character_id, True, is_first_attempt=False)
            if question.topic_id is not None:
                update_topic_mastery(db, user.id, question.topic_id, True, is_first_attempt=False)
            session.points_earned += points
            award_points(db, user, points, "correct_answer")
        else:
            question.is_correct = False

    db.commit()

    result = {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "points_earned": points,
        "question_number": question.question_number,
    }
    if bonus_text:
        result["bonus"] = bonus_text
    return result


def _update_car_level(user: User, settings) -> bool:
    """Check if user reached a new car tier. Returns True if leveled up."""
    thresholds = settings.car_tier_thresholds
    # Tiers are driven by lifetime earnings so store spending never blocks
    # progression
    total_coins = user.lifetime_coins or 0
    new_level = 0
    for i, threshold in enumerate(thresholds):
        if total_coins >= threshold:
            new_level = i
    if new_level > user.car_level:
        user.car_level = new_level
        return True
    return False


def _advance_quest(db: Session, user: User, settings) -> dict | None:
    """Advance quest progress after completing a session. Returns quest info or None."""
    from app.models.quest import QuestProgress

    qp = db.query(QuestProgress).filter_by(user_id=user.id).first()
    if not qp:
        qp = QuestProgress(user_id=user.id, season=1, stage=1, sessions_in_stage=0)
        db.add(qp)
        db.flush()

    qp.sessions_in_stage += 1
    quest_info = {
        "season": qp.season,
        "stage": qp.stage,
        "sessions_in_stage": qp.sessions_in_stage,
        "sessions_needed": settings.quest_sessions_per_stage,
        "stage_complete": False,
        "season_complete": False,
    }

    if qp.sessions_in_stage >= settings.quest_sessions_per_stage:
        # Stage complete
        quest_info["stage_complete"] = True
        award_points(db, user, settings.quest_stage_bonus_coins, "quest_stage_bonus")

        if qp.stage >= settings.quest_stages_per_season:
            # Season complete
            quest_info["season_complete"] = True
            award_points(db, user, settings.quest_season_bonus_coins, "quest_season_bonus")
            qp.season += 1
            qp.stage = 1
            qp.sessions_in_stage = 0
        else:
            qp.stage += 1
            qp.sessions_in_stage = 0

    return quest_info


def complete_session(db: Session, user: User, session_id: int) -> dict:
    """Complete a session and award bonuses."""
    session = _lock_for_scoring(db, user, GameSession.id == session_id, GameSession.user_id == user.id)
    if not session:
        raise ValueError("Session not found")

    if session.completed_at:
        raise ValueError("Session already completed")

    if any(q.selected_answer is None for q in session.questions):
        raise ValueError("Session has unanswered questions")

    session.completed_at = datetime.now(timezone.utc)

    # points_earned was accumulated per answer (incl. lucky-star/speed bonuses)
    settings = get_settings()
    total_questions = len(session.questions)
    base_points = session.points_earned or 0

    # Perfect session bonus
    is_perfect = session.total_correct == total_questions
    perfect_bonus = 0
    if is_perfect:
        perfect_bonus = base_points * (settings.perfect_bonus_multiplier - 1)
        if perfect_bonus > 0:
            award_points(db, user, perfect_bonus, "perfect_bonus")
            session.points_earned += perfect_bonus
        user.perfect_sessions += 1

    # Daily bonus (first completed session of the day)
    daily_bonus = 0
    if not _has_daily_bonus_award(db, user.id, date.today()):
        daily_bonus = settings.daily_bonus
        award_points(db, user, daily_bonus, "daily_bonus")
        session.points_earned += daily_bonus

    # Streak bonus
    streak_bonus = 0
    if user.streak > 0:
        streak_bonus = user.streak * settings.streak_bonus_multiplier
        award_points(db, user, streak_bonus, "streak_bonus")
        session.points_earned += streak_bonus

    # Update user stats
    user.total_sessions_completed += 1
    if user.streak > user.best_streak:
        user.best_streak = user.streak

    # Car level check
    car_leveled_up = _update_car_level(user, settings)

    # Quest progress
    quest_info = _advance_quest(db, user, settings)

    # Achievement check
    from app.services.achievements import check_badges
    session_result = {
        "total_correct": session.total_correct,
        "total_wrong": session.total_wrong,
    }
    new_badges = check_badges(db, user, session_result, session)

    # Daily quest updates
    from app.services.daily_quests import update_quest_progress
    completed_quests = []
    
    # Quest: play_session
    quest_result = update_quest_progress(db, user.id, "play_session", 1)
    if quest_result:
        completed_quests.append(quest_result)
    
    # Quest: perfect_session
    if is_perfect:
        quest_result = update_quest_progress(db, user.id, "perfect_session", 1)
        if quest_result:
            completed_quests.append(quest_result)
    
    # Quest: combo_master
    if session.max_combo >= 3:
        quest_result = update_quest_progress(db, user.id, "combo_master", 1)
        if quest_result:
            completed_quests.append(quest_result)
    
    # Quest: streak_keeper (check current streak)
    if user.streak >= 3:
        quest_result = update_quest_progress(db, user.id, "streak_keeper", 1)
        if quest_result:
            completed_quests.append(quest_result)

    db.commit()

    # Build XP breakdown
    xp_breakdown = []
    combo_bonus = session.combo_bonus or 0
    xp_breakdown.append({"label": "Correct answers", "value": base_points - combo_bonus})
    if combo_bonus > 0:
        xp_breakdown.append({"label": "Combo bonus", "value": combo_bonus})
    if perfect_bonus > 0:
        xp_breakdown.append({"label": "Perfect bonus", "value": perfect_bonus})
    if daily_bonus > 0:
        xp_breakdown.append({"label": "Daily bonus", "value": daily_bonus})
    if streak_bonus > 0:
        xp_breakdown.append({"label": f"Streak x{user.streak}", "value": streak_bonus})

    return {
        "session_id": session.id,
        "total_correct": session.total_correct,
        "total_wrong": session.total_wrong,
        "total_questions": total_questions,
        "points_earned": session.points_earned,
        "is_perfect": is_perfect,
        "streak": user.streak,
        "best_streak": user.best_streak,
        "total_points": user.points,
        "total_stars": user.stars,
        "total_coins": user.coins,
        "stars_to_next_coin": settings.coins_per_stars - (user.stars % settings.coins_per_stars),
        "car_level": user.car_level,
        "car_leveled_up": car_leveled_up,
        "perfect_sessions": user.perfect_sessions,
        "total_sessions_completed": user.total_sessions_completed,
        "max_combo": session.max_combo or 0,
        "combo_bonus": session.combo_bonus or 0,
        "xp_breakdown": xp_breakdown,
        "new_badges": new_badges,
        "quest": quest_info,
        "completed_quests": completed_quests,
    }
