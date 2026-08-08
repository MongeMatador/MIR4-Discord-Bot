from typing import Optional
from database.connection import DatabaseConnection
from config import logger

class LogRepository:
    """Repositório de persistência para o canal de logs."""

    async def set_log_channel(self, guild_id: int, category: str, channel_id: int) -> bool:
        try:
            async with DatabaseConnection.get_connection() as db:
                await db.execute("PRAGMA busy_timeout = 5000;")
                await db.execute("""
                    INSERT INTO guild_log_channels (guild_id, category, channel_id, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(guild_id, category) DO UPDATE SET
                        channel_id = excluded.channel_id,
                        updated_at = CURRENT_TIMESTAMP;
                """, (guild_id, category.upper(), channel_id))
                await db.commit()
            logger.info(f"[DB LOG SUCCESS] Guild: {guild_id} | Categoria: {category} | Canal: {channel_id}")
            return True
        except Exception as e:
            logger.error(f"[DB LOG ERROR] Falha ao gravar canal de log no banco: {e}", exc_info=True)
            return False

    async def get_log_channel_id(self, guild_id: int, category: str) -> Optional[int]:
        try:
            async with DatabaseConnection.get_connection() as db:
                await db.execute("PRAGMA busy_timeout = 5000;")
                async with db.execute(
                    "SELECT channel_id FROM guild_log_channels WHERE guild_id = ? AND category = ?",
                    (guild_id, category.upper())
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else None
        except Exception as e:
            logger.error(f"[DB LOG FETCH ERROR]: {e}", exc_info=True)
            return None
