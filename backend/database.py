
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from dotenv import load_dotenv


# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(PROJECT_ROOT / ".env")


# Connect to PostgreSQL

def get_connection():
    # The candidate backend uses a separate test database.
    database_name = os.getenv("DB_NAME", "")

    if os.getenv("AI_MODEL_NAME") == "random_forest_candidate.pkl":
        database_name = os.getenv(
            "TEST_DB_NAME",
            "disease_prediction_test_db",
        )

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=database_name,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )



# Save a prediction for the logged-in user
def save_prediction(
    symptoms: list[str],
    prediction: str,
    user_id: int,
    confidence: float = 0.0,
    severity: str = "Moderate",
    doctor_recommendation: Optional[str] = None,
    **kwargs,
) -> int:
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            symptoms_str = ", ".join(symptoms) if isinstance(symptoms, list) else str(symptoms)
            try:
                cursor.execute(
                    """
                    INSERT INTO prediction_history
                        (user_id, symptoms, prediction, confidence, severity, doctor_recommendation)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        symptoms_str,
                        prediction,
                        confidence,
                        severity,
                        doctor_recommendation or "General Physician",
                    ),
                )
            except Exception:
                connection.rollback()
                cursor.execute(
                    """
                    INSERT INTO prediction_history
                        (user_id, symptoms, prediction)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        symptoms_str,
                        prediction,
                    ),
                )

            row = cursor.fetchone()
            inserted_id = row[0] if row else 1

        connection.commit()
        return inserted_id

    except Exception:
        if connection is not None:
            connection.rollback()
        raise

    finally:
        if connection is not None:
            connection.close()


def get_prediction_history(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve the latest 100 predictions for one user."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, symptoms, prediction, created_at, confidence, severity, doctor_recommendation
                FROM prediction_history
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 100
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "symptoms": row[1],
                "prediction": row[2],
                "created_at": (
                    row[3].isoformat()
                    if row[3] is not None
                    else None
                ),
                "confidence": float(row[4]) if row[4] is not None else 0.0,
                "severity": row[5] or "Moderate",
                "doctor_recommendation": row[6] or "General Physician",
            }
            for row in rows
        ]

    finally:
        if connection is not None:
            connection.close()


def get_prediction_by_id(prediction_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single prediction by ID for the specific user."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, symptoms, prediction, created_at, confidence, severity, doctor_recommendation
                FROM prediction_history
                WHERE id = %s AND user_id = %s
                """,
                (prediction_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "symptoms": row[1],
                "prediction": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "confidence": float(row[4]) if row[4] is not None else 0.0,
                "severity": row[5] or "Moderate",
                "doctor_recommendation": row[6] or "General Physician",
            }
    finally:
        if connection is not None:
            connection.close()


def get_user_profile(user_id: int) -> Dict[str, Any]:
    """Retrieve patient health profile information."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.id, u.full_name, u.email, u.role, u.created_at,
                       p.age, p.gender, p.blood_group, p.phone, p.emergency_contact, p.allergies
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return {}

            return {
                "id": row[0],
                "full_name": row[1],
                "email": row[2],
                "role": row[3],
                "member_since": row[4].isoformat() if row[4] else None,
                "age": row[5],
                "gender": row[6],
                "blood_group": row[7],
                "phone": row[8],
                "emergency_contact": row[9],
                "allergies": row[10],
            }
    finally:
        if connection is not None:
            connection.close()


def save_user_profile(user_id: int, data: Dict[str, Any]) -> bool:
    """Create or update patient health profile."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_profiles
                    (user_id, age, gender, blood_group, phone, emergency_contact, allergies, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    blood_group = EXCLUDED.blood_group,
                    phone = EXCLUDED.phone,
                    emergency_contact = EXCLUDED.emergency_contact,
                    allergies = EXCLUDED.allergies,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    data.get("age"),
                    data.get("gender"),
                    data.get("blood_group"),
                    data.get("phone"),
                    data.get("emergency_contact"),
                    data.get("allergies"),
                ),
            )
        connection.commit()
        return True
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()


def get_doctors() -> List[Dict[str, Any]]:
    """Retrieve list of available verified doctors."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, specialty, experience_years, rating, clinic_address, contact_phone, is_available
                FROM doctors
                WHERE is_available = TRUE
                ORDER BY rating DESC, experience_years DESC
                """
            )
            rows = cursor.fetchall()

        return [
            {
                "id": r[0],
                "name": r[1],
                "specialty": r[2],
                "experience_years": r[3],
                "rating": float(r[4]),
                "clinic_address": r[5],
                "contact_phone": r[6],
                "is_available": r[7],
            }
            for r in rows
        ]
    finally:
        if connection is not None:
            connection.close()


def book_appointment(
    user_id: int,
    doctor_id: Optional[int],
    doctor_name: str,
    specialty: str,
    appointment_date: str,
    time_slot: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Book a doctor appointment."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO appointments
                    (user_id, doctor_id, doctor_name, specialty, appointment_date, time_slot, reason, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Confirmed')
                RETURNING id, created_at
                """,
                (
                    user_id,
                    doctor_id,
                    doctor_name,
                    specialty,
                    appointment_date,
                    time_slot,
                    reason or "AI Symptom Checker Follow-up",
                ),
            )
            row = cursor.fetchone()
        connection.commit()
        return {
            "id": row[0],
            "doctor_name": doctor_name,
            "specialty": specialty,
            "appointment_date": appointment_date,
            "time_slot": time_slot,
            "status": "Confirmed",
            "created_at": row[1].isoformat() if row[1] else None,
        }
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()


def get_user_appointments(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve appointments for a user."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, doctor_id, doctor_name, specialty, appointment_date, time_slot, reason, status, created_at
                FROM appointments
                WHERE user_id = %s
                ORDER BY appointment_date DESC, id DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        return [
            {
                "id": r[0],
                "doctor_id": r[1],
                "doctor_name": r[2],
                "specialty": r[3],
                "appointment_date": str(r[4]),
                "time_slot": r[5],
                "reason": r[6],
                "status": r[7],
                "created_at": r[8].isoformat() if r[8] else None,
            }
            for r in rows
        ]
    finally:
        if connection is not None:
            connection.close()


def cancel_appointment(appointment_id: int, user_id: int) -> bool:
    """Cancel an appointment."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE appointments
                SET status = 'Cancelled'
                WHERE id = %s AND user_id = %s
                """,
                (appointment_id, user_id),
            )
            updated = cursor.rowcount > 0
        connection.commit()
        return updated
    finally:
        if connection is not None:
            connection.close()


def get_health_tips() -> List[Dict[str, Any]]:
    """Retrieve health tips."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, category, title, content, icon
                FROM health_tips
                ORDER BY id ASC
                """
            )
            rows = cursor.fetchall()

        return [
            {
                "id": r[0],
                "category": r[1],
                "title": r[2],
                "content": r[3],
                "icon": r[4],
            }
            for r in rows
        ]
    finally:
        if connection is not None:
            connection.close()


# Test the PostgreSQL connection
if __name__ == "__main__":
    connection = None
    try:
        connection = get_connection()
        print("PostgreSQL connected successfully!")
    except psycopg2.Error:
        print("Database connection failed.")
        raise
    finally:
        if connection is not None:
            connection.close()
            print("Database connection closed.")
