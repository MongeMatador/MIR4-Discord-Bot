from config import logger

# Cria um alias 'log' para evitar quebras se algum arquivo importar 'log' ou 'logger'
log = logger

__all__ = ["logger", "log"]
