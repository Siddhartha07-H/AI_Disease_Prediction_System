"""
Unit tests for Database Operations
"""

from backend.database import (
    get_connection,
    get_doctors,
    get_health_tips,
    get_user_profile,
    save_prediction,
    get_prediction_history
)


def test_database_connection():
    conn = get_connection()
    assert conn is not None
    conn.close()


def test_database_doctors_seeding():
    docs = get_doctors()
    assert isinstance(docs, list)
    assert len(docs) >= 8
    first = docs[0]
    assert "name" in first
    assert "specialty" in first
    assert "rating" in first


def test_database_health_tips_seeding():
    tips = get_health_tips()
    assert isinstance(tips, list)
    assert len(tips) >= 6
    assert "title" in tips[0]
    assert "content" in tips[0]


def test_database_save_and_retrieve_prediction():
    user_id = 1
    sample_symptoms = ["fatigue", "high_fever", "headache"]
    sample_pred = "Dengue"

    rec_id = save_prediction(
        symptoms=sample_symptoms,
        prediction=sample_pred,
        user_id=user_id,
        confidence=92.5,
        severity="High",
        doctor_recommendation="Infectious Disease Specialist"
    )
    assert rec_id is not None
    assert rec_id > 0

    history = get_prediction_history(user_id)
    assert len(history) > 0
    matched = [h for h in history if h["id"] == rec_id]
    assert len(matched) == 1
    assert matched[0]["prediction"] == sample_pred
    assert matched[0]["confidence"] == 92.5
