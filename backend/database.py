
import atexit
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.pool import PoolError, ThreadedConnectionPool
from dotenv import load_dotenv

logger = logging.getLogger("healthai.database")

# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(PROJECT_ROOT / ".env")


# -------------------------------------------------------------
# High-Performance Threaded PostgreSQL Connection Pool
# Handles concurrent heavy traffic loads and prevents connection exhaustion
# -------------------------------------------------------------
_db_pool: Optional[ThreadedConnectionPool] = None
POOL_MIN_CONNECTIONS = int(os.getenv("DB_POOL_MIN", "2"))
POOL_MAX_CONNECTIONS = int(os.getenv("DB_POOL_MAX", "25"))


def _resolve_db_name() -> str:
    database_name = os.getenv("DB_NAME", "disease_prediction_db")
    if os.getenv("AI_MODEL_NAME") == "random_forest_candidate.pkl":
        database_name = os.getenv("TEST_DB_NAME", "disease_prediction_test_db")
    return database_name


def _resolve_sslmode() -> str:
    """
    Resolve SSL mode for PostgreSQL connection.
    Supports DB_SSLMODE environment variable.
    Defaults to 'require' for remote cloud databases (e.g. Supabase, Neon)
    and 'prefer' for local development.
    """
    configured = os.getenv("DB_SSLMODE")
    if configured:
        return configured
    host = os.getenv("DB_HOST", "localhost")
    return "prefer" if host in ("localhost", "127.0.0.1") else "require"


def get_db_pool() -> ThreadedConnectionPool:
    global _db_pool
    if _db_pool is None or _db_pool.closed:
        database_name = _resolve_db_name()
        timeout_sec = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
        sslmode = _resolve_sslmode()
        _db_pool = ThreadedConnectionPool(
            minconn=POOL_MIN_CONNECTIONS,
            maxconn=POOL_MAX_CONNECTIONS,
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=database_name,
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=timeout_sec,
            sslmode=sslmode,
        )
    return _db_pool


class PooledConnectionWrapper:
    """
    Transparent proxy for a pooled psycopg2 connection.
    Intercepts .close() to return the connection to the pool rather than
    terminating the underlying TCP socket.
    """
    def __init__(self, pool: ThreadedConnectionPool, conn):
        self._pool = pool
        self._conn = conn
        self._closed = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)

    def close(self):
        if not self._closed:
            self._closed = True
            try:
                if not self._conn.closed:
                    self._conn.rollback()
            except Exception:
                pass
            try:
                self._pool.putconn(self._conn)
            except Exception as exc:
                logger.warning(f"Failed to return connection to pool: {exc}")

    def __enter__(self):
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_connection():
    """
    Acquire a connection from the connection pool.
    Gracefully falls back to a direct connection if the pool is unavailable.
    """
    timeout_sec = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
    sslmode = _resolve_sslmode()
    try:
        pool = get_db_pool()
        raw_conn = pool.getconn()
        return PooledConnectionWrapper(pool, raw_conn)
    except Exception as exc:
        logger.warning(f"Connection pool unavailable, falling back to direct connection: {exc}")
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=_resolve_db_name(),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=timeout_sec,
            sslmode=sslmode,
        )


def close_db_pool():
    global _db_pool
    if _db_pool is not None and not _db_pool.closed:
        _db_pool.closeall()
        _db_pool = None


atexit.register(close_db_pool)




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


# -------------------------------------------------------------
# Doctor Management Functions
# -------------------------------------------------------------
def create_doctor_profile(
    user_id: int,
    name: str,
    specialty: str,
    experience_years: int = 5,
    clinic_address: str = "Medical Arts Pavilion",
    contact_phone: str = "+1 (800) 555-0199",
    license_number: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a linked doctor profile for a doctor user."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO doctors
                    (user_id, name, specialty, experience_years, rating, clinic_address, contact_phone, license_number, is_available)
                VALUES (%s, %s, %s, %s, 5.0, %s, %s, %s, TRUE)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    specialty = EXCLUDED.specialty,
                    experience_years = EXCLUDED.experience_years,
                    clinic_address = EXCLUDED.clinic_address,
                    contact_phone = EXCLUDED.contact_phone,
                    license_number = EXCLUDED.license_number
                RETURNING id, name, specialty, experience_years, rating, clinic_address, contact_phone, license_number, is_available
                """,
                (user_id, name, specialty, experience_years, clinic_address, contact_phone, license_number),
            )
            r = cursor.fetchone()
        connection.commit()
        return {
            "id": r[0],
            "name": r[1],
            "specialty": r[2],
            "experience_years": r[3],
            "rating": float(r[4]),
            "clinic_address": r[5],
            "contact_phone": r[6],
            "license_number": r[7],
            "is_available": r[8],
        }
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()


def get_doctor_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch doctor profile by associated user_id."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, name, specialty, experience_years, rating, clinic_address, contact_phone, license_number, is_available
                FROM doctors
                WHERE user_id = %s
                """,
                (user_id,),
            )
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "id": r[0],
                "user_id": r[1],
                "name": r[2],
                "specialty": r[3],
                "experience_years": r[4],
                "rating": float(r[5]),
                "clinic_address": r[6],
                "contact_phone": r[7],
                "license_number": r[8],
                "is_available": r[9],
            }
    finally:
        if connection is not None:
            connection.close()


def get_doctor_appointments(doctor_id: Optional[int], doctor_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all appointments assigned to a doctor along with patient clinical information."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.id, a.user_id, a.doctor_id, a.doctor_name, a.specialty,
                    a.appointment_date, a.time_slot, a.reason, a.status, a.notes, a.created_at,
                    u.full_name AS patient_name, u.email AS patient_email,
                    p.age AS patient_age, p.gender AS patient_gender, p.blood_group AS patient_blood_group,
                    p.phone AS patient_phone, p.allergies AS patient_allergies
                FROM appointments a
                LEFT JOIN users u ON a.user_id = u.id
                LEFT JOIN user_profiles p ON a.user_id = p.user_id
                WHERE (a.doctor_id = %s OR LOWER(a.doctor_name) = LOWER(%s))
                ORDER BY a.appointment_date DESC, a.id DESC
                """,
                (doctor_id, doctor_name or ""),
            )
            rows = cursor.fetchall()

        return [
            {
                "id": r[0],
                "patient_id": r[1],
                "doctor_id": r[2],
                "doctor_name": r[3],
                "specialty": r[4],
                "appointment_date": str(r[5]),
                "time_slot": r[6],
                "reason": r[7],
                "status": r[8],
                "notes": r[9],
                "created_at": r[10].isoformat() if r[10] else None,
                "patient": {
                    "name": r[11] or "Patient",
                    "email": r[12] or "N/A",
                    "age": r[13],
                    "gender": r[14],
                    "blood_group": r[15],
                    "phone": r[16],
                    "allergies": r[17],
                },
            }
            for r in rows
        ]
    finally:
        if connection is not None:
            connection.close()


def update_appointment_status(
    appointment_id: int,
    status_value: str,
    notes: Optional[str] = None,
    doctor_id: Optional[int] = None,
) -> bool:
    """Update appointment status (Confirmed, Completed, Cancelled) and optional clinical notes."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            if doctor_id:
                cursor.execute(
                    """
                    UPDATE appointments
                    SET status = %s, notes = COALESCE(%s, notes)
                    WHERE id = %s AND (doctor_id = %s OR doctor_id IS NULL)
                    """,
                    (status_value, notes, appointment_id, doctor_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE appointments
                    SET status = %s, notes = COALESCE(%s, notes)
                    WHERE id = %s
                    """,
                    (status_value, notes, appointment_id),
                )
            updated = cursor.rowcount > 0
        connection.commit()
        return updated
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()


def update_doctor_profile(
    doctor_id: int,
    is_available: Optional[bool] = None,
    contact_phone: Optional[str] = None,
    clinic_address: Optional[str] = None,
    specialty: Optional[str] = None,
) -> bool:
    """Update doctor profile and availability."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE doctors
                SET
                    is_available = COALESCE(%s, is_available),
                    contact_phone = COALESCE(%s, contact_phone),
                    clinic_address = COALESCE(%s, clinic_address),
                    specialty = COALESCE(%s, specialty)
                WHERE id = %s
                """,
                (is_available, contact_phone, clinic_address, specialty, doctor_id),
            )
            updated = cursor.rowcount > 0
        connection.commit()
        return updated
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
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

