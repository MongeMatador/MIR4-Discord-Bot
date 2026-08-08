from typing import Dict, List
from database.connection import DatabaseConnection


class ClaimRepository:
    """Gerencia a persistência das ocupações de Praça e Pico Secreto."""

    async def claim_spot(
        self, guild_id: int, spot_name: str, user_id: int, user_name: str
    ) -> bool:
        try:
            async with DatabaseConnection.get_connection() as db:
                await db.execute(
                    """
                    INSERT INTO active_claims (guild_id, spot_name, user_id, user_name)
                    VALUES (?, ?, ?, ?);
                """,
                    (guild_id, spot_name, user_id, user_name),
                )
                await db.commit()
            return True
        except Exception:
            return False

    async def unclaim_spot(
        self, guild_id: int, spot_name: str, user_id: int
    ) -> bool:
        async with DatabaseConnection.get_connection() as db:
            cursor = await db.execute(
                """
                DELETE FROM active_claims 
                WHERE guild_id = ? AND spot_name = ? AND user_id = ?;
            """,
                (guild_id, spot_name, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def clear_all_claims(self, guild_id: int):
        async with DatabaseConnection.get_connection() as db:
            await db.execute(
                "DELETE FROM active_claims WHERE guild_id = ?;", (guild_id,)
            )
            await db.commit()

    async def get_all_claims(self, guild_id: int) -> List[Dict]:
        async with DatabaseConnection.get_connection() as db:
            db.row_factory = aiosqlite.Row if hasattr(aiosqlite, "Row") else None
            async with db.execute(
                "SELECT spot_name, user_id, user_name, claimed_at FROM active_claims WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
