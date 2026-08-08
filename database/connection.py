import aiosqlite
from config import Config, logger

class DatabaseConnection:
    @staticmethod
    async def get_connection() -> aiosqlite.Connection:
        Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        db = await aiosqlite.connect(Config.DATABASE_PATH)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("PRAGMA journal_mode = WAL;")
        return db

    @staticmethod
    async def init_db():
        logger.info("Inicializando esquemas SQLite...")
        async with await DatabaseConnection.get_connection() as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS panel_settings (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

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
        logger.info("Esquemas de banco de dados inicializados com sucesso.")
