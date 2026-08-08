from typing import Optional
from database.connection import DatabaseConnection
from utils.logger import log

class LogRepository:
    """Gerencia a persistência dos canais de logs de claims e auditoria."""

    async def set_log_channel(self, guild_id: int, category: str, channel_id: int) -> bool:
        try:
            async with await DatabaseConnection.get_connection() as db:
                await db.execute("""
                    INSERT INTO guild_log_channels (guild_id, category, channel_id, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(guild_id, category) DO UPDATE SET
                        channel_id = excluded.channel_id,
                        updated_at = CURRENT_TIMESTAMP;
                """, (guild_id, category.upper(), channel_id))
                await db.commit()
            log.info(f"[DB LOG] Canal de log salvo: Guild {guild_id} | Categoria {category} | Canal {channel_id}")
            return True
        except Exception as e:
            log.error(f"[DB LOG ERROR] Falha ao salvar canal de log: {e}", exc_info=True)
            return False

    async def get_log_channel_id(self, guild_id: int, category: str) -> Optional[int]:
        async with await DatabaseConnection.get_connection() as db:
            async with db.execute(
                "SELECT channel_id FROM guild_log_channels WHERE guild_id = ? AND category = ?",
                (guild_id, category.upper())
            ) as cursor:
                row = await cursor.fetchone()
                return row["channel_id"] if row else None
