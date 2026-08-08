import aiosqlite
from config import DATABASE_PATH
from utils.logger import log

class DatabaseConnection:
    @staticmethod
    async def get_connection() -> aiosqlite.Connection:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        db = await aiosqlite.connect(DATABASE_PATH)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("PRAGMA journal_mode = WAL;")
        return db

    @staticmethod
    async def init_db():
        log.info("Inicializando esquemas de banco de dados no SQLite...")
        async with await DatabaseConnection.get_connection() as db:
            # Tabela de Painéis
            await db.execute("""
                CREATE TABLE IF NOT EXISTS panel_settings (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Tabela de Claims Ativos
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

            # Tabela de Canais de Logs
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
        log.info("Tabelas e índices verificados e prontos.")
