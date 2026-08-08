import aiosqlite
from config import Config, logger

class DatabaseConnection:
    """Gerenciador assíncrono de conexões do SQLite com tratamento anti-lock."""

    @staticmethod
    def get_connection():
        Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return aiosqlite.connect(Config.DATABASE_PATH)

    @staticmethod
    async def init_db():
        logger.info("Inicializando esquemas e tabelas do SQLite...")
        async with DatabaseConnection.get_connection() as db:
            db.row_factory = aiosqlite.Row
            
            # Configurações de segurança contra travamentos de disco
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("PRAGMA busy_timeout = 5000;")

            # Tabela de Configurações de Painel Único
            await db.execute("""
                CREATE TABLE IF NOT EXISTS panel_settings (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Tabela de Claims de Praça e Pico Secreto
            await db.execute("""
                CREATE TABLE IF NOT EXISTS active_claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    spot_name TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    user_name TEXT NOT NULL,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_guild_spot ON active_claims(guild_id, spot_name);")

            # Tabela de Canais de Logs de Auditoria
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_log_channels (
                    guild_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, category)
                );
            """)
            await db.commit()
        logger.info("Tabelas SQLite verificadas e prontas.")
