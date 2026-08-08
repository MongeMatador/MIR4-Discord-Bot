from typing import Optional, Tuple
from database.connection import DatabaseConnection
from config import logger


class PanelRepository:
    """Gerencia a persistência da mensagem do painel da guilda."""

    async def get_panel(self, guild_id: int) -> Optional[Tuple[int, int]]:
        async with DatabaseConnection.get_connection() as db:
            db.row_factory = aiosqlite.Row if hasattr(aiosqlite, "Row") else None
            async with db.execute(
                "SELECT channel_id, message_id FROM panel_settings WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row["channel_id"], row["message_id"]
                return None

    async def save_panel(self, guild_id: int, channel_id: int, message_id: int):
        async with DatabaseConnection.get_connection() as db:
            await db.execute(
                """
                INSERT INTO panel_settings (guild_id, channel_id, message_id, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(guild_id) DO UPDATE SET
                    channel_id = excluded.channel_id,
                    message_id = excluded.message_id,
                    updated_at = CURRENT_TIMESTAMP;
            """,
                (guild_id, channel_id, message_id),
            )
            await db.commit()
        logger.info(
            f"[DB PANEL] Referência salva: Guild {guild_id} | Msg {message_id}"
        )
