import json
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import GameSession, SessionQuestion
from app.services.question_generator import select_characters, generate_image_options, generate_options, generate_question, pick_question_mode
from app.services.spaced_repetition import update_mastery
from app.services.rewards import award_points
from app.config import get_settings


class SessionLimitReached(Exception):
    pass


def can_start_session(user: User) -> bool:
    """Check if user can start a new session today. 0 = unlimited."""
    user.reset_daily_if_needed()
    limit = get_settings().max_sessions_per_day
    if limit <= 0:
        return True
    return user.sessions_today < limit


def create_session(db: Session, user: User) -> GameSession:
    """Create a new game session with 5 questions."""
    user.reset_daily_if_needed()
    settings = get_settings()

    if settings.max_sessions_per_day > 0 and user.sessions_today >= settings.max_sessions_per_day:
        raise SessionLimitReached("Daily session limit reached. Come back tomorrow!")

    # Select characters and create session
    theme = user.theme or "racing"
    characters = select_characters(db, user.id, count=settings.questions_per_session, theme=theme)

    if not characters:
        raise ValueError("No characters available for this user.")

    game_session = GameSession(user_id=user.id)
    db.add(game_session)
    db.flush()  # Get the session ID

    # Create questions with mixed modes for variety
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
            selected_answer=None,
            is_correct=None,
        )
        db.add(question)

    # Update user session count
    user.sessions_today += 1
    user.last_played_date = date.today()

    db.commit()
    return game_session


def submit_answer(db: Session, user: User, question_id: int, selected_answer: str) -> dict:
    """Submit an answer for a question. Returns result dict."""
    question = db.query(SessionQuestion).filter_by(id=question_id).first()
    if not question:
        raise ValueError("Question not found")

    session = db.query(GameSession).filter_by(id=question.session_id).first()
    if session.user_id != user.id:
        raise ValueError("This question doesn't belong to you")

    if question.selected_answer is not None:
        raise ValueError("Question already answered")

    is_correct = selected_answer == question.correct_answer
    question.selected_answer = selected_answer
    question.is_correct = is_correct
    question.answered_at = datetime.now(timezone.utc)

    # Update mastery
    update_mastery(db, user.id, question.character_id, is_correct)

    # Award points
    settings = get_settings()
    points = settings.points_correct if is_correct else settings.points_wrong

    if is_correct:
        session.total_correct += 1
        award_points(db, user, points, "correct_answer")
    else:
        session.total_wrong += 1

    db.commit()

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "points_earned": points,
        "question_number": question.question_number,
    }


def complete_session(db: Session, user: User, session_id: int) -> dict:
    """Complete a session and award bonuses."""
    session = db.query(GameSession).filter_by(id=session_id, user_id=user.id).first()
    if not session:
        raise ValueError("Session not found")

    if session.completed_at:
        raise ValueError("Session already completed")

    session.completed_at = datetime.now(timezone.utc)

    # Calculate session points
    settings = get_settings()
    session.points_earned = session.total_correct * settings.points_correct

    # Daily bonus (first session of the day)
    if user.sessions_today == 1:
        award_points(db, user, settings.daily_bonus, "daily_bonus")
        session.points_earned += settings.daily_bonus

    # Streak bonus
    if user.streak > 0:
        streak_bonus = user.streak * settings.streak_bonus_multiplier
        award_points(db, user, streak_bonus, "streak_bonus")
        session.points_earned += streak_bonus

    db.commit()

    return {
        "session_id": session.id,
        "total_correct": session.total_correct,
        "total_wrong": session.total_wrong,
        "points_earned": session.points_earned,
        "streak": user.streak,
        "total_points": user.points,
        "total_stars": user.stars,
        "total_coins": user.coins,
    }
