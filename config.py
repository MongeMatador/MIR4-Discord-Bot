import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv("DISCORD_TOKEN")
    DB_PATH = "database.db"
    
    # Fuso horário do Servidor do Jogo (BRT - 1 hora = UTC-4)
    TIMEZONE_OFFSET = int(os.getenv("SERVER_TIMEZONE", "-4"))
    PORT = int(os.getenv("PORT", "8080"))
    
    MAX_QUEUE_SIZE = 3
    
    # URL oficial fornecida para o mapa do Pico Secreto
    SECRET_PEAK_MAP_URL = "https://cdn.discordapp.com/attachments/1525963683019362306/1525963733728497866/Gemini_Generated_Image_nuxpe7nuxpe7nuxp.png?ex=6a554bf9&is=6a53fa79&hm=2f58fe170fe5607c4be8ad0b764cf20929807014325df8a093db6e421cc51a9b&"
    
    # CRONÔMETROS DE EVENTOS: Configuração global de nomes e emojis
    TRACKABLE_EVENTS = {
        "MAGIC_SQUARE": {
            "L1": {"label": "L1", "emoji": "⚔️"},
            "L2": {"label": "L2", "emoji": "⚔️"},
            "SELAR": {"label": "Selar", "emoji": "🗡️"},
            "PLANTA": {"label": "Planta", "emoji": "🌿"},
            "MINERIO": {"label": "Minério", "emoji": "⛏️"}
        },
        "SECRET_PEAK": {
            "BOSS_ESQ": {"label": "Yellow Boss Left", "emoji": "⬅️"},
            "BOSS_DIR": {"label": "Yellow Boss Right", "emoji": "➡️"},
            "MINERIO_ELITE": {"label": "Minério Dourado", "emoji": "⛏️"},
            "SUMMON_EVENT": {"label": "Summon Events", "emoji": "🌀"},
            "SUMMON_GOBLIN": {"label": "Summon Goblin", "emoji": "👺"}
        }
    }
    
    # MATRIZ HORÁRIA: Contagens regressivas automáticas e alertas de 15 minutos
    FIXED_BOSS_HOURS = {
        "SECRET_PEAK": {
            "DEFAULT": {
                "SUL": ["01:00", "07:00", "13:00", "19:00"],
                "NORTE": ["04:00", "10:00", "16:00", "22:00"]
            },
            "11F": {
                "NORTE": ["01:00", "13:00"],
                "SUL": ["07:00", "19:00"]
            },
            "12F": {
                "NORTE": ["01:00", "13:00"],
                "SUL": ["07:00", "19:00"]
            }
        },
        "MAGIC_SQUARE": {
            "DEFAULT": {
                "LÍDER_3": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
            },
            "11F": {
                "LÍDER_3": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
                "FÚRIA": ["00:30", "03:30", "06:30", "09:30", "12:30", "15:30", "18:30", "21:30"],
                "FRENZY": ["02:00", "05:00", "08:00", "11:00", "14:00", "17:00", "20:00", "23:00"]
            },
            "12F": {
                "LÍDER_3": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
                "FÚRIA": ["00:30", "03:30", "06:30", "09:30", "12:30", "15:30", "18:30", "21:30"],
                "FRENZY": ["02:00", "05:00", "08:00", "11:00", "14:00", "17:00", "20:00", "23:00"]
            }
        }
    }
    
    MAP_DATA = {
        "MAGIC_SQUARE": {
            "label": "🔮 Praça Mágica",
            "floors": {
                "6F": {
                    "ANTIDEMON": {"rooms": 3, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🚪"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "👑"}
                },
                "7F": {
                    "ANTIDEMON": {"rooms": 3, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🚪"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "👑"}
                },
                "8F": {
                    "ANTIDEMON": {"rooms": 3, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🚪"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "👑"}
                },
                "9F": {
                    "ANTIDEMON 1": {"rooms": 3, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🚪"},
                    "ANTIDEMON 2": {"rooms": 3, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🚪"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "👑"}
                },
                "10F": {
                    "ANTIDEMON 1": {"rooms": 3, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🚪"},
                    "ANTIDEMON 2": {"rooms": 3, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🚪"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "👑"}
                },
                "11F": {
                    "ANTIDEMON": {"rooms": 3, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🚪"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "👑"},
                    "FRENZY": {"rooms": 1, "tickets": [1, 2], "allow_queue": False, "emoji": "🔥"},
                    "FURY": {"rooms": 1, "tickets": [1, 2], "allow_queue": False, "emoji": "⚡"},
                    "SUMMON GOBLIN": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "👺"}
                },
                "12F": {
                    "ANTIDEMON": {"rooms": 3, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🚪"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "👑"},
                    "FRENZY": {"rooms": 1, "tickets": [1, 2], "allow_queue": False, "emoji": "🔥"},
                    "FURY": {"rooms": 1, "tickets": [1, 2], "allow_queue": False, "emoji": "⚡"},
                    "SUMMON GOBLIN": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "👺"}
                }
            }
        },
        "SECRET_PEAK": {
            "label": "🏔️ Pico Secreto",
            "floors": {
                "6F": {
                    "A1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "A2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "SUMMON": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🌀"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "🐲"}
                },
                "7F": {
                    "A1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "A2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "SUMMON": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🌀"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "🐲"}
                },
                "8F": {
                    "A1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "A2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "SUMMON": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🌀"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "🐲"}
                },
                "9F": {
                    "A1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "A2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "SUMMON": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🌀"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "🐲"}
                },
                "10F": {
                    "A1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "A2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "N2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S1": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "S2": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🗺️"},
                    "SUMMON": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🌀"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "🐲"}
                },
                "11F": {
                    "SUMMON GOBLIN": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "👺"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "🐲"}
                },
                "12F": {
                    "SUMMON GOBLIN": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "👺"},
                    "SUMMON EVENTS": {"rooms": 1, "tickets": [1, 3, 6], "allow_queue": True, "emoji": "🌀"},
                    "BOSS": {"rooms": 1, "tickets": [1, 2, 3], "allow_queue": True, "emoji": "🐲"}
                }
            }
        }
    }
    FLOOR_LAYOUT = MAP_DATA["MAGIC_SQUARE"]["floors"]

    @staticmethod
    def get_valid_events_for_floor(map_type: str, floor: str) -> list:
        if map_type == "MAGIC_SQUARE":
            if floor in ["11F", "12F"]:
                return ["L1", "L2"]
            return ["L1", "L2", "SELAR", "PLANTA", "MINERIO"]
        elif map_type == "SECRET_PEAK":
            if floor in ["11F", "12F"]:
                # CORRIGIDO: Ativa o monitoramento tático de Yellow Boss Left e Yellow Boss Right no 11F/12F do Pico
                return ["BOSS_ESQ", "BOSS_DIR"]
            return ["BOSS_ESQ", "BOSS_DIR", "MINERIO_ELITE"]
        return []