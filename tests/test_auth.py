"""
Unit tests for Authentication and JWT Security
"""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

from backend.auth import create_access_token, password_hasher
import jwt


def test_password_hasher():
    raw_password = "ClinicalSecurePassword2026!"
    hashed = password_hasher.hash(raw_password)

    assert hashed != raw_password
    assert password_hasher.verify(raw_password, hashed) is True
    assert password_hasher.verify("WrongPassword", hashed) is False


def test_jwt_token_creation_and_decoding():
    user_id = 999
    role = "patient"
    token = create_access_token(user_id=user_id, role=role)

    assert isinstance(token, str)
    assert len(token) > 20

    secret = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    decoded = jwt.decode(token, secret, algorithms=[algorithm])
    assert decoded["sub"] == str(user_id)
    assert decoded["role"] == role
    assert "exp" in decoded
    assert "iat" in decoded
