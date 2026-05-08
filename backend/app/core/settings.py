from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Load project-level and app-level environment variables when the app starts.
BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "backend" / ".env", override=True)
load_dotenv(BASE_DIR / "rag" / ".env", override=False)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./intra_q.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-dev-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

ALLOWED_ORIGINS = [
	"http://localhost:5173",
	"http://127.0.0.1:5173",
	"http://localhost:3000",
]
