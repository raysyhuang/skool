import json
import random
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import GameSession, SessionQuestion
from app.models.rewards import PointsLedger
from app.services.question_generator import select_characters, generate_image_options, generate_options, generate_question, pick_question_mode
from app.services.spaced_repetition import update_mastery
from app.services.rewards import award_points
from app.services.math_generator import generate_math_questions
from app.services.logic_generator import generate_logic_questions
from app.services.english_generator import generate_english_questions
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


def create_session(db: Session, user: User, game_type: str = "chinese") -> GameSession:
    """Create a new game session with 5 questions."""
    user.reset_daily_if_needed()
    settings = get_settings()

    if settings.max_sessions_per_day > 0 and user.sessions_today >= settings.max_sessions_per_day:
        raise SessionLimitReached("Daily session limit reached. Come back tomorrow!")

    game_session = GameSession(user_id=user.id, game_type=game_type)
    db.add(game_session)
    db.flush()

    if game_type == "chinese":
        _create_chinese_questions(db, game_session, user, settings)
    elif game_type == "math":
        _create_math_questions(db, game_session, user, settings)
    elif game_type == "logic":
        _create_logic_questions(db, game_session, user, settings)
    elif game_type == "english":
        _create_english_questions(db, game_session, user, settings)
    else:
        raise ValueError(f"Unknown game type: {game_type}")

    # Update user session count
    user.sessions_today += 1
    user.last_played_date = date.today()

    db.commit()
    return game_session


def _create_chinese_questions(db: Session, game_session: GameSession, user: User, settings) -> None:
    """Create Chinese character questions (original logic)."""
    theme = user.theme or "racing"
    characters = select_characters(db, user.id, count=settings.questions_per_session, theme=theme)

    if not characters:
        raise ValueError("No characters available for this user.")

    for i, char in enumerate(characters, 1):
        mode = pick_question_mode(theme, char)
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


def _create_math_questions(db: Session, game_session: GameSession, user: User, settings) -> None:
    """Create math questions based on user age."""
    age = user.age or 5
    math_qs = generate_math_questions(age, count=settings.questions_per_session)

    for i, mq in enumerate(math_qs, 1):
        question = SessionQuestion(
            session_id=game_session.id,
            character_id=None,
            question_number=i,
            correct_answer=mq["correct_answer"],
            options=json.dumps(mq["options"]),
            question_mode=mq["mode"],
            prompt_data=mq["prompt_data"],
        )
        db.add(question)


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


def _create_english_questions(db: Session, game_session: GameSession, user: User, settings) -> None:
    """Create English language questions based on user age."""
    age = user.age or 5
    eng_qs = generate_english_questions(age, count=settings.questions_per_session)

    for i, eq in enumerate(eng_qs, 1):
        question = SessionQuestion(
            session_id=game_session.id,
            character_id=None,
            question_number=i,
            correct_answer=eq["correct_answer"],
            options=json.dumps(eq["options"]),
            question_mode=eq["mode"],
            prompt_data=eq["prompt_data"],
        )
        db.add(question)


def submit_answer(db: Session, user: User, question_id: int, selected_answer: str) -> dict:
    """Submit an answer for a question. Returns result dict."""
    question = db.query(SessionQuestion).filter_by(id=question_id).first()
    if not question:
        raise ValueError("Question not found")

    session = db.query(GameSession).filter_by(id=question.session_id).first()
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

        # Update mastery on first answer attempt
        if question.character_id is not None:
            update_mastery(db, user.id, question.character_id, is_correct)

        if is_correct:
            points = settings.points_correct

            # Lucky star: random chance of multiplied points
            if random.random() < settings.lucky_star_chance:
                points *= settings.lucky_star_multiplier
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
                update_mastery(db, user.id, question.character_id, True)
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
    # Calculate total coins ever earned (current coins + spent coins approximation)
    # We use current coins as a simple proxy
    total_coins = user.coins
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
    session = db.query(GameSession).filter_by(id=session_id, user_id=user.id).first()
    if not session:
        raise ValueError("Session not found")

    if session.completed_at:
        raise ValueError("Session already completed")

    if any(q.selected_answer is None for q in session.questions):
        raise ValueError("Session has unanswered questions")

    session.completed_at = datetime.now(timezone.utc)

    # Calculate session points
    settings = get_settings()
    total_questions = len(session.questions)
    session.points_earned = session.total_correct * settings.points_correct

    # Perfect session bonus
    is_perfect = session.total_correct == total_questions
    perfect_bonus = 0
    if is_perfect:
        perfect_bonus = session.points_earned * (settings.perfect_bonus_multiplier - 1)
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

    db.commit()

    # Build XP breakdown
    xp_breakdown = []
    base_xp = session.total_correct * settings.points_correct
    xp_breakdown.append({"label": "Correct answers", "value": base_xp})
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
        "xp_breakdown": xp_breakdown,
        "new_badges": new_badges,
        "quest": quest_info,
    }
