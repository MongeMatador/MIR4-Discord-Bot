import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
import colorlog

# Carrega variáveis do arquivo .env caso exista localmente
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
        """Valida se as variáveis de ambiente essenciais estão presentes."""
        if not cls.DISCORD_TOKEN:
            raise ValueError(
                "CRÍTICO: A variável de ambiente DISCORD_TOKEN não foi encontrada!\n"
                "Certifique-se de adicioná-la nas 'Environment Variables' do seu painel no Render."
            )

def setup_logger() -> logging.Logger:
    """Configura o sistema de logs colorido para o console e arquivo local."""
    logger = logging.getLogger("MIR4Bot")
    logger.setLevel(Config.LOG_LEVEL)

    # Evita duplicidade de handlers em reloads
    if logger.handlers:
        return logger

    # Handler para o Console do Render
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

# Instância de logger pronta para importação
logger = setup_logger()
