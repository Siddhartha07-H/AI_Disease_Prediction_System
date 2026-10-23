# Production Multi-Stage Dockerfile for HealthAI System
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies for PostgreSQL and building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Run database initializer and launch FastAPI with Uvicorn
EXPOSE 8000

CMD ["sh", "-c", "python database/init_db.py && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
