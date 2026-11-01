"""Placeholder placement test service for PR #14."""

from sqlalchemy.orm import Session
from app.models import User


def start_placement_test(db: Session, user: User, subject: str):
    """Start placement test."""
    from app.models.placement import PlacementTest
    test = PlacementTest(user_id=user.id, subject=subject)
    db.add(test)
    db.commit()
    return test


def get_next_placement_question(db: Session, test):
    """Get next question."""
    if len(test.responses) >= 10:
        return None
    
    return {
        "question_number": len(test.responses) + 1,
        "question_data": {
            "prompt": "What is 2 + 2?",
            "expression": "2 + 2",
            "options": ["3", "4", "5", "6"]
        }
    }


def submit_placement_response(db: Session, test, question_data, selected_answer, response_time_ms):
    """Submit answer."""
    from app.models.placement import PlacementResponse
    
    correct = selected_answer == "4"
    response = PlacementResponse(
        test_id=test.id,
        question_data=str(question_data),
        selected_answer=selected_answer,
        is_correct=correct,
        response_time_ms=response_time_ms
    )
    db.add(response)
    db.commit()
    
    return {"correct": correct}


def complete_placement_test(db: Session, test):
    """Complete test."""
    from app.models.placement import SkillAbility
    
    correct_count = sum(1 for r in test.responses if r.is_correct)
    accuracy = correct_count / len(test.responses) if test.responses else 0
    ability = 1000 + (accuracy - 0.5) * 400
    
    skill_ability = SkillAbility(
        user_id=test.user_id,
        subject=test.subject,
        ability=ability
    )
    db.add(skill_ability)
    db.commit()
    
    return {
        "recommended_grade": 3,
        "accuracy": accuracy,
        "estimated_ability": ability
    }
