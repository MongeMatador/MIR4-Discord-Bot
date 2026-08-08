import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import colorlog

# Carrega variáveis de ambiente
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Configurações globais centralizadas da aplicação e dados de salas do MIR4."""
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "database/mir4_bot.db")
    PORT: int = int(os.getenv("PORT", "8080"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Game-specific settings
    SECRET_PEAK_MAP_URL = "https://cdn.discordapp.com/attachments/1525963683019362306/1525963733728497866/Gemini_Generated_Image_nuxpe7nuxpe7nuxp.png?ex=6a554bf9&is=6a53fa79&hm=2f58fe170fe5607c4be8ad0b764cf20929807014325df8a093db6e421cc51a9b&"
    MAX_QUEUE_SIZE = 3
    TIMEZONE_OFFSET = int(os.getenv("SERVER_TIMEZONE", "-4"))

    # Fixed Boss Timers (UTC-4) in English
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
                "SOUTH": ["01:00", "07:00", "13:00", "19:00"],
                "NORTH": ["04:00", "10:00", "16:00", "22:00"]
            },
            "11F": {
                "SOUTH": ["07:00", "19:00"],
                "NORTH": ["01:00", "13:00"]
            },
            "12F": {
                "SOUTH": ["07:00", "19:00"],
                "NORTH": ["01:00", "13:00"]
            }
        }
    }

    # Rotation trackable events in English
    TRACKABLE_EVENTS = {
        "MAGIC_SQUARE": {
            "L1": {"label": "L1", "emoji": "⚔️"},
            "L2": {"label": "L2", "emoji": "⚔️"},
            "SEAL": {"label": "SEAL", "emoji": "🗡️"},
            "PLANT": {"label": "PLANT", "emoji": "🌿"},
            "GOLDEN_ORE": {"label": "GOLDEN ORE", "emoji": "⛏️"}
        },
        "SECRET_PEAK": {
            "YELLOW_BOSS_LEFT": {"label": "YELLOW BOSS LEFT", "emoji": "⬅️"},
            "YELLOW_BOSS_RIGHT": {"label": "YELLOW BOSS RIGHT", "emoji": "➡️"},
            "GOLDEN_ORE": {"label": "GOLDEN ORE", "emoji": "⛏️"}
        }
    }

    @classmethod
    def get_valid_events_for_floor(cls, map_type: str, floor: str):
        if map_type == "MAGIC_SQUARE" and floor in ["11F", "12F"]:
            return ["L1", "L2"]
        if map_type == "SECRET_PEAK" and floor in ["11F", "12F"]:
            return []
        return list(cls.TRACKABLE_EVENTS.get(map_type, {}).keys())

    # MAGIC SQUARE: Lower floors setup (6F to 10F)
    MS_ADC_SPOTS = {
        "ADC1": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": list((1, 2, 3))},
        "ADC2": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": list((1, 2, 3))},
        "ADC3": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": list((1, 2, 3))},
        "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": list((1, 2, 3))}
    }

    # MAGIC SQUARE: High floors setup (11F and 12F) with 3 ADCs and 3-Ticket Fury/Frenzy
    MS_HIGH_SPOTS = {
        "ADC1": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": list((1, 2, 3))},
        "ADC2": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": list((1, 2, 3))},
        "ADC3": {"rooms": 3, "emoji": "🚪", "allow_queue": True, "tickets": list((1, 2, 3))},
        "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": list((1, 2, 3))},
        "FURY": {"rooms": 1, "emoji": "⚡", "allow_queue": False, "tickets": list((1, 2, 3))},
        "FRENZY": {"rooms": 1, "emoji": "🔥", "allow_queue": False, "tickets": list((1, 2, 3))},
        "SUMMON GOBLIN": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": list((1, 2, 3))}
    }

    # SECRET PEAK: Default Spots setup (6F to 10F) [cite: 5, 6, 7]
    PS_DEFAULT_SPOTS = {
        "A1": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": list((1, 2, 3))},
        "A2": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": list((1, 2, 3))},
        "N1": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": list((1, 2, 3))},
        "N2": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": list((1, 2, 3))},
        "S1": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": list((1, 2, 3))},
        "S2": {"rooms": 1, "emoji": "📍", "allow_queue": True, "tickets": list((1, 2, 3))},
        "SUMMON": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": list((1, 2, 3))},
        "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": list((1, 2, 3))}
    }

    MAP_DATA = {
        "MAGIC_SQUARE": {
            "label": "🔮 Magic Square",
            "floors": {
                "6F": MS_ADC_SPOTS,
                "7F": MS_ADC_SPOTS,
                "8F": MS_ADC_SPOTS,
                "9F": MS_ADC_SPOTS,
                "10F": MS_ADC_SPOTS,
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
                "11F": {
                    "SUMMON GOBLIN": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": list((1, 2, 3))},
                    "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": list((1, 2, 3))}
                },
                "12F": {
                    "SUMMON GOBLIN": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": list((1, 2, 3))},
                    "SUMMON EVENTS": {"rooms": 1, "emoji": "🌀", "allow_queue": True, "tickets": list((1, 2, 3))},
                    "BOSS": {"rooms": 1, "emoji": "👑", "allow_queue": True, "tickets": list((1, 2, 3))}
                }
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
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
