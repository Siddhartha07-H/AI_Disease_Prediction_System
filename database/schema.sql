-- ====================================================================
-- AI Disease Prediction System - Database Schema
-- Compatible with PostgreSQL (Production) and SQLite (Development/Fallback)
-- ====================================================================

-- 1. Users table (Stores patient and doctor credentials)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'patient',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. User Profiles table (Extended patient health profile)
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    gender VARCHAR(20),
    blood_group VARCHAR(10),
    phone VARCHAR(30),
    emergency_contact VARCHAR(100),
    allergies TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Prediction History table (Stores symptom checks and AI diagnostic outputs)
CREATE TABLE IF NOT EXISTS prediction_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symptoms TEXT NOT NULL,
    prediction TEXT NOT NULL,
    confidence NUMERIC(5, 2) DEFAULT 0.0,
    severity VARCHAR(50) DEFAULT 'Moderate',
    doctor_recommendation VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Doctors table (Verified specialists for appointment booking)
CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    specialty VARCHAR(150) NOT NULL,
    experience_years INTEGER DEFAULT 10,
    rating NUMERIC(3, 1) DEFAULT 4.9,
    clinic_address VARCHAR(255) DEFAULT 'Metro Health Center, Suite 400',
    contact_phone VARCHAR(50) DEFAULT '+1 (800) 555-0199',
    license_number VARCHAR(100),
    is_available BOOLEAN DEFAULT TRUE
);

-- 5. Appointments table (Patient doctor appointments)
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    doctor_id INTEGER REFERENCES doctors(id) ON DELETE SET NULL,
    doctor_name VARCHAR(150) NOT NULL,
    specialty VARCHAR(150) NOT NULL,
    appointment_date DATE NOT NULL,
    time_slot VARCHAR(50) NOT NULL,
    reason TEXT,
    status VARCHAR(50) DEFAULT 'Confirmed',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Health Tips table (Curated preventive healthcare content)
CREATE TABLE IF NOT EXISTS health_tips (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    icon VARCHAR(50) DEFAULT 'heart'
);

-- Schema upgrades for existing installations
ALTER TABLE prediction_history ADD COLUMN IF NOT EXISTS confidence NUMERIC(5, 2) DEFAULT 0.0;
ALTER TABLE prediction_history ADD COLUMN IF NOT EXISTS severity VARCHAR(50) DEFAULT 'Moderate';
ALTER TABLE prediction_history ADD COLUMN IF NOT EXISTS doctor_recommendation VARCHAR(150);

ALTER TABLE doctors ADD COLUMN IF NOT EXISTS user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE doctors ADD COLUMN IF NOT EXISTS license_number VARCHAR(100);
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS notes TEXT;

