"""Auto-load .env on import.

The cloud routine harness injects env vars directly, so `load_dotenv` is a no-op
there. Locally it picks up `.env` at the repo root regardless of cwd.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
