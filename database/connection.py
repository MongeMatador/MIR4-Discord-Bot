import aiosqlite
from config import Config, logger

class DatabaseManager:
    @staticmethod
    def get_connection():
        Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return aiosqlite.connect(Config.DATABASE_PATH)

    @staticmethod
    async def initialize():
        logger.info("Inicializando esquemas e tabelas do SQLite (Clean Advanced)...")
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("PRAGMA busy_timeout = 5000;")

            # Tabela de Configurações de Painéis Principais (Claims de cliques)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS panel_settings (
                guild_id INTEGER NOT NULL,
                map_type TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, map_type)
            );
            """)

            # Tabela de Canais de Status de Andares (Os placares públicos)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS floor_dashboards (
                guild_id INTEGER NOT NULL,
                map_type TEXT NOT NULL,
                floor TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, map_type, floor)
            );
            """)

            # Tabela de Claims ativas
            await db.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                map_type TEXT NOT NULL,
                floor TEXT NOT NULL,
                spot_type TEXT NOT NULL,
                room_number INTEGER NOT NULL,
                status TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                started_at TIMESTAMP NOT NULL,
                ends_at TIMESTAMP NOT NULL,
                tickets INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Tabela de Fila de Espera
            await db.execute("""
            CREATE TABLE IF NOT EXISTS spot_queues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                map_type TEXT NOT NULL,
                floor TEXT NOT NULL,
                spot_type TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                tickets INTEGER NOT NULL,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Tabela de Eventos de Respawn (L1, L2, etc.)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS floor_events (
                guild_id INTEGER NOT NULL,
                map_type TEXT NOT NULL,
                floor TEXT NOT NULL,
                event_name TEXT NOT NULL,
                last_triggered_at TIMESTAMP,
                last_triggered_by INTEGER,
                PRIMARY KEY (guild_id, map_type, floor, event_name)
            );
            """)

            # Tabela de Canais de Logs de Auditoria da Staff
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
