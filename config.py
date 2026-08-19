import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Configurações globais centralizadas da aplicação e dados de salas do MIR4."""
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "database/mir4_bot.db")
    PORT: int = int(os.getenv("PORT", "8080"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Game-specific settings
    SECRET_PEAK_MAP_URL = "https://github.com/MongeMatador/MIR4-Discord-Bot/blob/main/ui/Mapa%20Pico%20Secreto.png?raw=true"
    MAX_QUEUE_SIZE = 3
    TIMEZONE_OFFSET = int(os.getenv("SERVER_TIMEZONE", "-4"))

    # Fixed Boss Timers (UTC-4)
    FIXED_BOSS_HOURS = {
        "MAGIC_SQUARE": {
            "DEFAULT": {
                "LEADER_3": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
            },
            "11F": {
                "LEADER_3": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
                "FURY": ["00:30", "03:30", "06:30", "09:30", "12:30", "15:30", "18:30", "21:30"],
                "FRENZY": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
            },
            "12F": {
                "LEADER_3": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
                "FURY": ["00:30", "03:30", "06:30", "09:30", "12:30", "15:30", "18:30", "21:30"],
                "FRENZY": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
            }
        },
        "SECRET_PEAK": {
            "DEFAULT": {
                "SUL": ["01:00", "07:00", "13:00", "19:00"],
                "NORTE": ["04:00", "10:00", "16:00", "22:00"]
            },
            "11F": {
                "SUL": ["07:00", "19:00"],
                "NORTE": ["01:00", "13:00"]
            },
            "12F": {
                "SUL": ["07:00", "19:00"],
                "NORTE": ["01:00", "13:00"]
            }
        }
    }

    # Rotation trackable events
    TRACKABLE_EVENTS = {
        "MAGIC_SQUARE": {
            "L1": {"label": "L1", "emoji": "⚔️"},
            "L2": {"label": "L2", "emoji": "⚔️"},
            "MINERIO_DOURADO": {"label": "Minério Dourado", "emoji": "⛏️"},
            "PLANTA": {"label": "Planta", "emoji": "🌿"},
            "SELAR": {"label": "Selar", "emoji": "🗡️"}
        },
        "SECRET_PEAK": {
            "YELLOW_BOSS_LEFT": {"label": "Yellow Boss Left", "emoji": "⬅️"},
            "YELLOW_BOSS_RIGHT": {"label": "Yellow Boss Right", "emoji": "➡️"},
            "MINERIO_DOURADO": {"label": "Minério Dourado", "emoji": "⛏️"}
        }
    }

    @classmethod
    def get_valid_events_for_floor(cls, map_type: str, floor: str):
        if map_type == "MAGIC_SQUARE":
            if floor in ["11F", "12F"]:
                return ["L1", "L2"]
            return ["L1", "L2", "MINERIO_DOURADO", "PLANTA", "SELAR"]
        elif map_type == "SECRET_PEAK":
            if floor in ["11F", "12F"]:
                return []
            return ["YELLOW_BOSS_LEFT", "YELLOW_BOSS_RIGHT", "MINERIO_DOURADO"]
        return []

    # MAPA DA PRAÇA: do 6F ao 8F (1 ADC com 3 sub-salas), do 9F ao 10F (2 ADCs), 11F/12F (3 ADCs + fury/frenzy)
    MS_LOW_SPOTS = {
        "ADC1": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": [1, 3, 6]},
        "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": [1, 3]}
    }

    MS_MID_SPOTS = {
        "ADC1": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": [1, 3, 6]},
        "ADC2": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": [1, 3, 6]},
        "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": [1, 3]}
    }

    MS_HIGH_SPOTS = {
        "ADC1": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": [1, 3, 6]},
        "ADC2": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": [1, 3, 6]},
        "ADC3": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": [1, 3, 6]},
        "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": [1, 3]},
        "FURY": {"rooms": 1, "emoji": "⚡", "allow_queue": False, "tickets": [1, 2, 3]},
        "FRENZY": {"rooms": 1, "emoji": "🔥", "allow_queue": False, "tickets": [1, 2, 3]},
        "SUMMON GOBLIN": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": [1, 3]}
    }

    # PICO SECRETO: 6F ao 10F (Coordenadas geográficas táticas com teto de 6 tickets e 3 para o Boss)
    PS_DEFAULT_SPOTS = {
        "A1": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": [1, 3, 6]},
        "A2": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": [1, 3, 6]},
        "N1": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": [1, 3, 6]},
        "N2": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": [1, 3, 6]},
        "S1": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": [1, 3, 6]},
        "S2": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": [1, 3, 6]},
        "SUMMON": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": [1, 3]},
        "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": [1, 3]}
    }

    # PICO SECRETO: 11F
    PS_11F_SPOTS = {
        "SUMMON GOBLIN": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": [1, 3]},
        "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": [1, 3]}
    }

    # PICO SECRETO: 12F
    PS_12F_SPOTS = {
        "SUMMON GOBLIN": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": [1, 3]},
        "SUMMON EVENTS": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": [1, 3]},
        "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": [1, 3]}
    }

    MAP_DATA = {
        "MAGIC_SQUARE": {
            "label": "🔮 Magic Square",
            "floors": {
                "6F": MS_LOW_SPOTS,
                "7F": MS_LOW_SPOTS,
                "8F": MS_LOW_SPOTS,
                "9F": MS_MID_SPOTS,
                "10F": MS_MID_SPOTS,
                "11F": MS_HIGH_SPOTS,
                "12F": MS_HIGH_SPOTS
            }
        },
        "SECRET_PEAK": {
            "label": "🏔️ Secret Peak",
            "floors": {
                "6F": PS_DEFAULT_SPOTS,
                "7F": PS_DEFAULT_SPOTS,
                "8F": PS_DEFAULT_SPOTS,
                "9F": PS_DEFAULT_SPOTS,
                "10F": PS_DEFAULT_SPOTS,
                "11F": PS_11F_SPOTS,
                "12F": PS_12F_SPOTS
            }
        }
    }

    @classmethod
    def validate(cls):
        if not cls.DISCORD_TOKEN:
            raise ValueError(
                "CRÍTICO: A variável DISCORD_TOKEN não foi encontrada!\n"
                "Configure a chave DISCORD_TOKEN nas Environment Variables do Render."
            )

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("MIR4Bot")
    logger.setLevel(Config.LOG_LEVEL)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s]: %(message)s"))
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
