from __future__ import annotations

import os

from dotenv import load_dotenv


# Load environment variables from the local .env file when the app starts.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./intra_q.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
