import os
import sys
import logging
from typing import Dict, Any

class Config:
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    CLIENT_ID: int = int(os.getenv("CLIENT_ID", "0"))
    GUILD_ID: int = int(os.getenv("GUILD_ID", "0"))
    PORT: int = int(os.getenv("PORT", "10000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DB_PATH: str = os.getenv("DB_PATH", "mars_bot.db")

# Exporta atalho minúsculo para evitar ImportError no bot.py
config = Config

def setup_logger() -> logging.Logger:
    log_inst = logging.getLogger("MARS_BOT")
    if log_inst.hasHandlers():
        return log_inst

    log_inst.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    log_inst.addHandler(console_handler)

    return log_inst

logger = setup_logger()

def build_antidemon_chambers(count: int) -> Dict[str, Any]:
    chambers = {}
    for ad_num in range(1, count + 1):
        ad_key = f"ANTIDEMON {ad_num}"
        chambers[ad_key] = {
            "rooms": ["Sala 1", "Sala 2", "Sala 3"]
        }
    return chambers

MAP_DATA: Dict[str, Any] = {
    "MAGIC_SQUARE": {
        "name": "Magic Square",
        "emoji": "🔮",
        "floors": {
            f"{i}F": {
                "standard_rooms": [
                    "Boss Room 1", "Boss Room 2",
                    "Chamber of Experience 1", "Chamber of Experience 2",
                    "Training Chamber 1", "Training Chamber 2",
                    "Gold Chamber", "Gathering Chamber"
                ],
                "antidemons": {}
            } for i in range(1, 13)
        }
    },
    "SECRET_PEAK": {
        "name": "Secret Peak",
        "emoji": "🏔️",
        "floors": {
            f"{i}F": {
                "standard_rooms": [
                    "Boss Room 1", "Boss Room 2",
                    "Chamber of Experience 1", "Chamber of Experience 2",
                    "Training Chamber 1", "Training Chamber 2",
                    "Gold Chamber", "Gathering Chamber"
                ]
            } for i in range(1, 13)
        }
    }
}

# Injeção Exata de Antidemônios da Cópia Original
MAP_DATA["MAGIC_SQUARE"]["floors"]["7F"]["antidemons"] = build_antidemon_chambers(1)
MAP_DATA["MAGIC_SQUARE"]["floors"]["8F"]["antidemons"] = build_antidemon_chambers(1)
MAP_DATA["MAGIC_SQUARE"]["floors"]["9F"]["antidemons"] = build_antidemon_chambers(2)
MAP_DATA["MAGIC_SQUARE"]["floors"]["10F"]["antidemons"] = build_antidemon_chambers(2)
MAP_DATA["MAGIC_SQUARE"]["floors"]["11F"]["antidemons"] = build_antidemon_chambers(3)
MAP_DATA["MAGIC_SQUARE"]["floors"]["12F"]["antidemons"] = build_antidemon_chambers(3)
