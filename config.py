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
    """Configurações globais centralizadas da aplicação."""
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "database/mir4_bot.db")
    PORT: int = int(os.getenv("PORT", 8080))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

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
