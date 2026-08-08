from typing import List, Dict
import aiosqlite
from database.connection import DatabaseConnection
from config import logger

class ClaimRepository:
    """Repositório de persistência das ocupações de Praça e Pico."""

    async def claim_spot(self, guild_id: int, spot_name: str, user_id: int, user_name: str) -> bool:
        try:
            async with DatabaseConnection.get_connection() as db:
                await db.execute("PRAGMA busy_timeout = 5000;")
                await db.execute("""
                    INSERT INTO active_claims (guild_id, spot_name, user_id, user_name)
                    VALUES (?, ?, ?, ?);
                """, (guild_id, spot_name, user_id, user_name))
                await db.commit()
            return True
        except Exception as e:
            logger.warning(f"[DB CLAIM FAILED] Spot {spot_name} ocupado ou erro: {e}")
            return False

    async def unclaim_spot(self, guild_id: int, spot_name: str, user_id: int) -> bool:
        try:
            async with DatabaseConnection.get_connection() as db:
                await db.execute("PRAGMA busy_timeout = 5000;")
                cursor = await db.execute("""
                    DELETE FROM active_claims 
                    WHERE guild_id = ? AND spot_name = ? AND user_id = ?;
                """, (guild_id, spot_name, user_id))
                await db.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"[DB UNCLAIM ERROR]: {e}", exc_info=True)
            return False

    async def clear_all_claims(self, guild_id: int):
        try:
            async with DatabaseConnection.get_connection() as db:
                await db.execute("PRAGMA busy_timeout = 5000;")
                await db.execute("DELETE FROM active_claims WHERE guild_id = ?;", (guild_id,))
                await db.commit()
        except Exception as e:
            logger.error(f"[DB CLEAR CLAIMS ERROR]: {e}", exc_info=True)

    async def get_all_claims(self, guild_id: int) -> List[Dict]:
        try:
            async with DatabaseConnection.get_connection() as db:
                db.row_factory = aiosqlite.Row
                await db.execute("PRAGMA busy_timeout = 5000;")
                async with db.execute(
                    "SELECT spot_name, user_id, user_name, claimed_at FROM active_claims WHERE guild_id = ?",
                    (guild_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"[DB GET ALL CLAIMS ERROR]: {e}", exc_info=True)
            return []
