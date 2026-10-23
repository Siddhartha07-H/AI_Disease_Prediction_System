
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import jwt
import psycopg2
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from psycopg2.errors import UniqueViolation
from pwdlib import PasswordHash

from backend.database import create_doctor_profile, get_connection, get_doctor_by_user_id


# -----------------------------
# Load environment configuration
# -----------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_MINUTES = 60 * 24  # 24 hours for seamless clinical session

router = APIRouter(tags=["Authentication"])
password_hasher = PasswordHash.recommended()


# -----------------------------
# Request models
# -----------------------------

class RegisterInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class DoctorRegisterInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    specialty: str = Field(min_length=2, max_length=150)
    experience_years: int = Field(default=5, ge=0, le=60)
    clinic_address: str = Field(default="Medical Arts Pavilion, Suite 300", max_length=255)
    contact_phone: str = Field(default="+1 (800) 555-0199", max_length=50)
    license_number: Optional[str] = Field(default=None, max_length=100)


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


# -----------------------------
# JWT access token creation
# -----------------------------

def create_access_token(user_id: int, role: str) -> str:
    if not JWT_SECRET_KEY or JWT_SECRET_KEY == "PASTE_SECRET_HERE":
        raise HTTPException(
            status_code=500,
            detail="JWT authentication is not configured correctly.",
        )

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


# -----------------------------
# Patient registration
# -----------------------------

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register_patient(data: RegisterInput):
    full_name = data.full_name.strip()
    email = str(data.email).strip().lower()

    if len(full_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please enter a valid full name.",
        )

    password_hash = password_hasher.hash(data.password)
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users
                    (full_name, email, password_hash, role)
                VALUES (%s, %s, %s, 'patient')
                RETURNING id, full_name, email, role, created_at
                """,
                (full_name, email, password_hash),
            )

            user = cursor.fetchone()

        connection.commit()

        return {
            "message": "Patient registered successfully.",
            "user": {
                "id": user[0],
                "full_name": user[1],
                "email": user[2],
                "role": user[3],
                "created_at": (
                    user[4].isoformat()
                    if isinstance(user[4], datetime)
                    else user[4]
                ),
            },
        }

    except UniqueViolation:
        if connection is not None:
            connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    except psycopg2.Error:
        if connection is not None:
            connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the account. Please try again.",
        )

    finally:
        if connection is not None:
            connection.close()


# -----------------------------
# Doctor registration
# -----------------------------

@router.post(
    "/doctor/register",
    status_code=status.HTTP_201_CREATED,
)
def register_doctor(data: DoctorRegisterInput):
    full_name = data.full_name.strip()
    email = str(data.email).strip().lower()

    if len(full_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please enter a valid full name.",
        )

    password_hash = password_hasher.hash(data.password)
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users
                    (full_name, email, password_hash, role)
                VALUES (%s, %s, %s, 'doctor')
                RETURNING id, full_name, email, role, created_at
                """,
                (full_name, email, password_hash),
            )
            user = cursor.fetchone()

        connection.commit()

        user_id = user[0]

        # Create linked doctor profile
        doc_profile = create_doctor_profile(
            user_id=user_id,
            name=f"Dr. {full_name}" if not full_name.lower().startswith("dr.") else full_name,
            specialty=data.specialty.strip(),
            experience_years=data.experience_years,
            clinic_address=data.clinic_address.strip(),
            contact_phone=data.contact_phone.strip(),
            license_number=data.license_number.strip() if data.license_number else None,
        )

        access_token = create_access_token(user_id=user_id, role="doctor")

        return {
            "message": "Doctor account registered and verified successfully.",
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_MINUTES * 60,
            "user": {
                "id": user[0],
                "full_name": user[1],
                "email": user[2],
                "role": "doctor",
                "created_at": (
                    user[4].isoformat()
                    if isinstance(user[4], datetime)
                    else user[4]
                ),
            },
            "doctor": doc_profile,
        }

    except UniqueViolation:
        if connection is not None:
            connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    except psycopg2.Error as exc:
        if connection is not None:
            connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to register doctor account. Please verify your details or try again later.",
        )

    finally:
        if connection is not None:
            connection.close()


# -----------------------------
# Unified Login (Patient & Doctor)
# -----------------------------

@router.post("/login")
def login_patient(data: LoginInput):
    email = str(data.email).strip().lower()
    connection = None
    user = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    full_name,
                    email,
                    password_hash,
                    role,
                    is_active
                FROM users
                WHERE LOWER(email) = %s
                """,
                (email,),
            )

            user = cursor.fetchone()

    except psycopg2.Error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process login. Please try again.",
        )

    finally:
        if connection is not None:
            connection.close()

    # Verify credentials
    if user is None or not password_hasher.verify(
        data.password,
        user[3],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Reject inactive accounts
    if not user[5]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive. Contact the administrator.",
        )

    role = user[4] or "patient"

    # Create signed token
    access_token = create_access_token(
        user_id=user[0],
        role=role,
    )

    doctor_info = None
    if role == "doctor":
        doctor_info = get_doctor_by_user_id(user[0])

    return {
        "message": "Login successful.",
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_MINUTES * 60,
        "user": {
            "id": user[0],
            "full_name": user[1],
            "email": user[2],
            "role": role,
        },
        "doctor": doctor_info,
    }


# Doctor specific alias for login
@router.post("/doctor/login")
def login_doctor(data: LoginInput):
    res = login_patient(data)
    if res["user"]["role"] != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is registered as a patient. Please use the Patient Login portal.",
        )
    return res

