import aiosqlite
from config import Config, logger


class DatabaseConnection:
    """Gerenciador de Conexão com o Banco de Dados SQLite Assíncrono (aiosqlite)."""

    @staticmethod
    def get_connection():
        """Retorna a conexão assíncrona configurada com o banco SQLite em modo WAL."""
        Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return aiosqlite.connect(Config.DATABASE_PATH)

    @staticmethod
    async def init_db():
        """Inicializa as tabelas do sistema garantindo uma única Thread do aiosqlite por execução."""
        logger.info("Inicializando infraestrutura e esquema do banco SQLite...")

        async with DatabaseConnection.get_connection() as db:
            db.row_factory = aiosqlite.Row

            # Ativa Foreign Keys e modo WAL para alta concorrência
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute("PRAGMA journal_mode = WAL;")

            # Tabela do Painel Único da Guilda
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS panel_settings (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            # Tabela de Claims de Praça e Pico
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS active_claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    spot_name TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    user_name TEXT NOT NULL,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            await db.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_guild_spot 
                ON active_claims(guild_id, spot_name);
            """
            )

            # Tabela de Canais de Logs
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS guild_log_channels (
                    guild_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, category)
                );
            """
            )

            await db.commit()

        logger.info("Banco de dados inicializado com sucesso (WAL Mode).")
