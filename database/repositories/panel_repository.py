from typing import Optional, Tuple
import aiosqlite
from database.connection import DatabaseConnection
from config import logger

class PanelRepository:
    """Repositório de persistência das mensagens do painel."""

    async def get_panel(self, guild_id: int) -> Optional[Tuple[int, int]]:
        try:
            async with DatabaseConnection.get_connection() as db:
                await db.execute("PRAGMA busy_timeout = 5000;")
                async with db.execute(
                    "SELECT channel_id, message_id FROM panel_settings WHERE guild_id = ?", 
                    (guild_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return row[0], row[1]
                    return None
        except Exception as e:
            logger.error(f"[DB PANEL FETCH ERROR]: {e}", exc_info=True)
            return None

    async def save_panel(self, guild_id: int, channel_id: int, message_id: int):
        try:
            async with DatabaseConnection.get_connection() as db:
                await db.execute("PRAGMA busy_timeout = 5000;")
                await db.execute("""
                    INSERT INTO panel_settings (guild_id, channel_id, message_id, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(guild_id) DO UPDATE SET
                        channel_id = excluded.channel_id,
                        message_id = excluded.message_id,
                        updated_at = CURRENT_TIMESTAMP;
                """, (guild_id, channel_id, message_id))
                await db.commit()
            logger.info(f"[DB PANEL SAVE] Painel registrado para Guild {guild_id}: Msg {message_id}")
        except Exception as e:
            logger.error(f"[DB PANEL SAVE ERROR]: {e}", exc_info=True)
