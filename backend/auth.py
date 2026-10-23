
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import psycopg2
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from psycopg2.errors import UniqueViolation
from pwdlib import PasswordHash

from backend.database import get_connection


# -----------------------------
# Load environment configuration
# -----------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_MINUTES = 30

router = APIRouter(tags=["Authentication"])
password_hasher = PasswordHash.recommended()


# -----------------------------
# Request models
# -----------------------------

class RegisterInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


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
# Patient login
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

    # Verify the credentials
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

    # Create a signed token after successful authentication
    access_token = create_access_token(
        user_id=user[0],
        role=user[4],
    )

    return {
        "message": "Login successful.",
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_MINUTES * 60,
        "user": {
            "id": user[0],
            "full_name": user[1],
            "email": user[2],
            "role": user[4],
        },
    }
