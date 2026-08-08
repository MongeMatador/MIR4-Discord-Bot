import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("CRÍTICO: DISCORD_TOKEN não configurado no .env!")

DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "database/mir4_bot.db")
PORT = int(os.getenv("PORT", 8080))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
