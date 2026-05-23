"""Shared config — loads .env from repo root."""
import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

MIMO_BASE_URL = os.environ["MIMO_BASE_URL"]
MIMO_API_KEY = os.environ["MIMO_API_KEY"]
MIMO_MODEL = os.environ["MIMO_MODEL"]
