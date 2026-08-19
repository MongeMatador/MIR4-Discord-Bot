import discord
import aiosqlite
from datetime import datetime, timedelta
from database.connection import DatabaseManager
from config import Config, logger

class ClaimService:
    def __init__(self, bot, log_service, panel_service):
        self.bot = bot
        self.log_service = log_service
        self.panel_service = panel_service

    @staticmethod
    async def get_floor_events(map_type: str, floor: str) -> list:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM floor_events WHERE map_type = ? AND floor = ?",
                (map_type, floor)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    @staticmethod
    async def get_queue_list(map_type: str, floor: str, spot_type: str) -> list:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM spot_queues WHERE map_type = ? AND floor = ? AND spot_type = ? ORDER BY queued_at ASC",
                (map_type, floor, spot_type)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    @staticmethod
    async def get_next_in_queue(map_type: str, floor: str, spot_type: str) -> dict:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM spot_queues WHERE map_type = ? AND floor = ? AND spot_type = ? ORDER BY queued_at ASC LIMIT 1",
                (map_type, floor, spot_type)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    @staticmethod
    async def remove_from_queue(queue_id: int):
        async with DatabaseManager.get_connection() as db:
            await db.execute("DELETE FROM spot_queues WHERE id = ?", (queue_id,))
            await db.commit()

    @staticmethod
    async def create_claim(guild_id: int, user_id: int, username: str, map_type: str, floor: str, spot_type: str, room_number: int, tickets: int):
        now = datetime.utcnow()
        ends = now + timedelta(minutes=tickets * 30)
        async with DatabaseManager.get_connection() as db:
            await db.execute(
                "INSERT INTO claims (guild_id, map_type, floor, spot_type, room_number, status, user_id, username, started_at, ends_at, tickets) VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?, ?)",
                (guild_id, map_type, floor, spot_type, room_number, user_id, username, now.isoformat(), ends.isoformat(), tickets)
            )
            await db.commit()

    async def register_claim(self, guild_id: int, user: discord.User, map_type: str, floor: str, spot_type: str, room_number: int, tickets: int) -> tuple:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            
            # Sanitiza os slots órfãos
            async with db.execute(
                "SELECT COUNT(*) FROM spot_queues WHERE guild_id = ? AND map_type = ? AND floor = ? AND spot_type = ?",
                (guild_id, map_type, floor, spot_type)
            ) as count_cursor:
                row = await count_cursor.fetchone()
                q_size = row[0] if row else 0
            
            if q_size == 0:
                await db.execute(
                    "UPDATE claims SET status = 'CANCELLED' WHERE guild_id = ? AND map_type = ? AND floor = ? AND spot_type = ? AND room_number = ? AND status = 'VACANT_REMAINING'",
                    (guild_id, map_type, floor, spot_type, room_number)
                )
                await db.commit()

            # Validação Multi-Contas por mapa (Permite um no Pico e um na Praça)
            async with db.execute(
                "SELECT * FROM claims WHERE guild_id = ? AND map_type = ? AND user_id = ? AND status = 'ACTIVE'",
                (guild_id, map_type, user.id)
            ) as cursor:
                active = await cursor.fetchone()
                if active:
                    return False, f"❌ **Falhou!** Você já possui uma sala ativa em **{map_type.replace('_', ' ')}**!"

            # Busca se o spot desejado já está ocupado
            async with db.execute(
                "SELECT * FROM claims WHERE guild_id = ? AND map_type = ? AND floor = ? AND spot_type = ? AND room_number = ? AND status IN ('ACTIVE', 'VACANT_REMAINING')",
                (guild_id, map_type, floor, spot_type, room_number)
            ) as cursor:
                occupied = await cursor.fetchone()

            if occupied:
                # Se for tempo restante, assume direto
                if occupied["status"] == "VACANT_REMAINING":
                    await db.execute(
                        "UPDATE claims SET status = 'ACTIVE', user_id = ?, username = ? WHERE id = ?",
                        (user.id, user.display_name, occupied["id"])
                    )
                    await db.commit()
                    await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
                    await self.log_service.dispatch_claim_log(guild_id, user, map_type, floor, spot_type, room_number, "CLAIM_VACANT", "Assumiu tempo restante")
                    return True, f"✅ **Sucesso!** Você assumiu o tempo restante de `{floor} - {spot_type}` (Sala {room_number})."

                # Se ocupado ativo, entra na fila se for elegível
                spot_info = Config.MAP_DATA[map_type]["floors"][floor][spot_type]
                if spot_info.get("allow_queue", True):
                    if q_size >= Config.MAX_QUEUE_SIZE:
                        return False, f"❌ **Fila Cheia!** O limite de {Config.MAX_QUEUE_SIZE} pessoas na fila foi atingido."

                    await db.execute(
                        "INSERT INTO spot_queues (guild_id, map_type, floor, spot_type, user_id, username, tickets) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (guild_id, map_type, floor, spot_type, user.id, user.display_name, tickets)
                    )
                    await db.commit()
                    await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
                    return True, f"👥 **Fila de Espera!** Você entrou na fila para o spot **{spot_type}**."
                else:
                    return False, "❌ **Ocupado!** Fila de espera desabilitada para eventos rápidos Frenzy/Fury."

            # Se livre, cria a claim normalmente
            now = datetime.utcnow()
            ends = now + timedelta(minutes=tickets * 30)
            await db.execute(
                "INSERT INTO claims (guild_id, map_type, floor, spot_type, room_number, status, user_id, username, started_at, ends_at, tickets) VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?, ?)",
                (guild_id, map_type, floor, spot_type, room_number, user.id, user.display_name, now.isoformat(), ends.isoformat(), tickets)
            )
            await db.commit()
            
        await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
        await self.log_service.dispatch_claim_log(guild_id, user, map_type, floor, spot_type, room_number, "CLAIM", f"Tickets: {tickets} ({tickets * 30}m)")
        return True, f"✅ **Sucesso!** Spot `{floor} - {spot_type}` (Sala {room_number}) reservado."

    async def release_claim(self, guild_id: int, user: discord.User, map_type: str) -> str:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM claims WHERE guild_id = ? AND map_type = ? AND user_id = ? AND status = 'ACTIVE'",
                (guild_id, map_type, user.id)
            ) as cursor:
                claim = await cursor.fetchone()

            if not claim:
                # Se não tem ativo, remove se estiver na fila
                async with db.execute(
                    "SELECT * FROM spot_queues WHERE guild_id = ? AND map_type = ? AND user_id = ?",
                    (guild_id, map_type, user.id)
                ) as cursor:
                    in_q = await cursor.fetchone()
                if in_q:
                    await db.execute("DELETE FROM spot_queues WHERE id = ?", (in_q["id"],))
                    await db.commit()
                    await self.panel_service.update_floor_dashboard(guild_id, map_type, in_q["floor"])
                    return f"✅ Você saiu da fila de espera do spot **{in_q['spot_type']}**."
                return "⚠️ Você não possui claims ativos ou posições em filas."

            floor = claim["floor"]
            spot_type = claim["spot_type"]
            room_number = claim["room_number"]

            # Vemos se há fila ativa
            queue_list = await self.get_queue_list(map_type, floor, spot_type)
            if queue_list:
                # Mantém em VACANT_REMAINING (Transferência de tempo restante)
                await db.execute("UPDATE claims SET status = 'VACANT_REMAINING' WHERE id = ?", (claim["id"],))
                await db.commit()
                msg = f"✅ Você liberou o spot **{spot_type}**. Ele virou **Tempo Restante** no placar!"
            else:
                await db.execute("UPDATE claims SET status = 'CANCELLED' WHERE id = ?", (claim["id"],))
                await db.commit()
                msg = f"✅ Você desocupou o spot **{spot_type}**!"

        await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
        await self.log_service.dispatch_claim_log(guild_id, user, map_type, floor, spot_type, room_number, "RELEASE")
        return msg

    async def trigger_floor_event(self, guild_id: int, user: discord.User, map_type: str, floor: str, event_key: str) -> tuple:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM claims WHERE guild_id = ? AND map_type = ? AND floor = ? AND spot_type = 'BOSS' AND status = 'ACTIVE'",
                (guild_id, map_type, floor)
            ) as cursor:
                boss_owner = await cursor.fetchone()

            if boss_owner and boss_owner["user_id"] != user.id:
                return False, f"⚠️ **Acesso Negado!** Somente o dono legítimo do BOSS (<@{boss_owner['user_id']}>) pode gerenciar as rotações deste andar."

            now = datetime.utcnow()
            await db.execute("""
                INSERT INTO floor_events (guild_id, map_type, floor, event_name, last_triggered_at, last_triggered_by)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, map_type, floor, event_name) DO UPDATE SET
                    last_triggered_at = excluded.last_triggered_at,
                    last_triggered_by = excluded.last_triggered_by;
            """, (guild_id, map_type, floor, event_key, now.isoformat(), user.id))
            await db.commit()

        await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
        return True, f"✅ Rotação de **{event_key}** atualizada para as {now.strftime('%H:%M')}!"
