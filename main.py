"""
Root FastAPI Entrypoint
Allows standard IDE execution, FastAPI CLI (`fastapi dev` / `fastapi run`),
and direct Python startup (`python main.py`).
"""

import os
import sys
from pathlib import Path

# Ensure project root is in Python module search path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Export 'app' so FastAPI auto-discovery finds it at the default location
from backend.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting HealthAI Server on http://{host}:{port} ...")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
