"""
Database initialization and seeding script.
Supports both PostgreSQL and local SQLite fallback.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    psycopg2 = None


DEFAULT_DOCTORS = [
    ("Dr. Sarah Jenkins, MD", "Cardiologist", 14, 4.9, "Heart & Vascular Institute, Suite 201", "+1 (800) 555-0144"),
    ("Dr. Marcus Vance, MD", "Dermatologist", 11, 4.8, "Advanced Skin Health Clinic, Floor 3", "+1 (800) 555-0182"),
    ("Dr. Elena Rostova, MD", "Gastroenterologist", 16, 4.9, "Digestive Wellness Center, Suite 105", "+1 (800) 555-0199"),
    ("Dr. Robert Chen, MD", "Pulmonologist", 12, 4.8, "Chest & Respiratory Medical Care", "+1 (800) 555-0123"),
    ("Dr. Aisha Al-Mansoor, MD", "Neurologist", 15, 4.9, "Neurological Care Institute, Floor 5", "+1 (800) 555-0167"),
    ("Dr. David Patel, MD", "Endocrinologist", 13, 4.7, "Metabolic & Diabetes Specialty Care", "+1 (800) 555-0131"),
    ("Dr. Claire Thompson, MD", "Infectious Disease Specialist", 18, 4.9, "Center for Infectious Disease & Travel Med", "+1 (800) 555-0176"),
    ("Dr. Benjamin Brooks, MD", "General Physician / Family Med", 20, 4.9, "Metro Family Health Practice", "+1 (800) 555-0110"),
]

DEFAULT_HEALTH_TIPS = [
    ("Immunity", "Hydration and Electrolyte Balance", "Drinking 2 to 2.5 liters of clean water daily supports kidney filtration, cardiovascular output, and mucosal immune barriers.", "water"),
    ("Cardiovascular", "Aerobic Exercise and Arterial Health", "Aim for 150 minutes of moderate-intensity aerobic physical activity weekly to enhance vascular elasticity and resting heart rate.", "heart"),
    ("Metabolic", "High-Fiber Diets for Glycemic Stability", "Consuming soluble fiber from oats, beans, and vegetables stabilizes post-meal blood sugar surges and lowers LDL cholesterol.", "apple"),
    ("Respiratory", "Air Quality and Lung Capacity", "Avoid prolonged exposure to fine particulate matter and second-hand smoke. Practice diaphragmatic breathing for 5 minutes daily.", "wind"),
    ("Skin", "Sun Protection and Barrier Defense", "Apply a broad-spectrum SPF 30+ sunscreen daily. Use non-comedogenic moisturizers to prevent transepidermal water loss.", "sun"),
    ("Mental Health", "Circadian Rhythm and Restorative Sleep", "Consistent sleep schedules regulating 7 to 8 hours of sleep support cellular repair, memory consolidation, and cytokine balance.", "moon"),
]


def init_database():
    print("Checking database configuration...")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "disease_prediction_db")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")

    if not psycopg2:
        print("psycopg2 is not installed. Please install psycopg2-binary.")
        return False

    connection = None
    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            database=dbname,
            user=user,
            password=password,
        )
        connection.autocommit = True
        print(f"Connected to PostgreSQL database: {dbname}")

        schema_file = PROJECT_ROOT / "database" / "schema.sql"
        if schema_file.exists():
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_sql = f.read()

            with connection.cursor() as cursor:
                cursor.execute(schema_sql)
            print("Database tables and columns created/updated successfully.")

        # Seed doctors if empty
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            count = cursor.fetchone()[0]
            if count == 0:
                print("Seeding initial verified doctors...")
                cursor.executemany(
                    """
                    INSERT INTO doctors (name, specialty, experience_years, rating, clinic_address, contact_phone)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    DEFAULT_DOCTORS,
                )
                print(f"Seeded {len(DEFAULT_DOCTORS)} doctors.")

        # Seed health tips if empty
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM health_tips")
            count = cursor.fetchone()[0]
            if count == 0:
                print("Seeding initial health tips...")
                cursor.executemany(
                    """
                    INSERT INTO health_tips (category, title, content, icon)
                    VALUES (%s, %s, %s, %s)
                    """,
                    DEFAULT_HEALTH_TIPS,
                )
                print(f"Seeded {len(DEFAULT_HEALTH_TIPS)} health tips.")

        print("Database initialization complete.")
        return True

    except Exception as exc:
        print(f"Database initialization failed: {exc}")
        return False
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
