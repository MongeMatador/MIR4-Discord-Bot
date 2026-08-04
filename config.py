import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configurações de Ambiente
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
    CLIENT_ID = int(os.getenv("CLIENT_ID", "0"))
    GUILD_ID = int(os.getenv("GUILD_ID", "0"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PORT = int(os.getenv("PORT", "10000"))

    # Estrutura do Mapa Original
    MAP_DATA = {
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
                    ]
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

# Mapeamento do Antidemônio Original (7F ao 10F)
# Fora do bloco da classe para não dar NameError
for f in range(7, 9):
    Config.MAP_DATA["MAGIC_SQUARE"]["floors"][f"{f}F"]["adc_rooms"] = ["Antidemônio 1"]

for f in range(9, 11):
    Config.MAP_DATA["MAGIC_SQUARE"]["floors"][f"{f}F"]["adc_rooms"] = ["Antidemônio 1", "Antidemônio 2"]

for f in range(11, 13):
    Config.MAP_DATA["MAGIC_SQUARE"]["floors"][f"{f}F"]["adc_rooms"] = ["Antidemônio 1"]
