import discord
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
        async with await DatabaseManager.get_connection() as conn:
            rows = await conn.fetch(
                "SELECT * FROM floor_events WHERE map_type = $1 AND floor = $2",
                map_type, floor
            )
            return [dict(r) for r in rows]

    @staticmethod
    async def get_queue_list(map_type: str, floor: str, spot_type: str) -> list:
        async with await DatabaseManager.get_connection() as conn:
            rows = await conn.fetch(
                "SELECT * FROM spot_queues WHERE map_type = $1 AND floor = $2 AND spot_type = $3 ORDER BY queued_at ASC",
                map_type, floor, spot_type
            )
            return [dict(r) for r in rows]

    @staticmethod
    async def get_next_in_queue(map_type: str, floor: str, spot_type: str) -> dict:
        async with await DatabaseManager.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM spot_queues WHERE map_type = $1 AND floor = $2 AND spot_type = $3 ORDER BY queued_at ASC LIMIT 1",
                map_type, floor, spot_type
            )
            return dict(row) if row else None

    @staticmethod
    async def remove_from_queue(queue_id: int):
        async with await DatabaseManager.get_connection() as conn:
            await conn.execute("DELETE FROM spot_queues WHERE id = $1", queue_id)

    @staticmethod
    async def create_claim(guild_id: int, user_id: int, username: str, map_type: str, floor: str, spot_type: str, room_number: int, tickets: int):
        now = datetime.utcnow()
        ends = now + timedelta(minutes=tickets * 30)
        async with await DatabaseManager.get_connection() as conn:
            await conn.execute("""
                INSERT INTO claims (guild_id, map_type, floor, spot_type, room_number, status, user_id, username, started_at, ends_at, tickets)
                VALUES ($1, $2, $3, $4, $5, 'ACTIVE', $6, $7, $8, $9, $10)
            """, guild_id, map_type, floor, spot_type, room_number, user_id, username, now, ends, tickets)

    async def register_claim(self, guild_id: int, user: discord.User, map_type: str, floor: str, spot_type: str, tickets: int) -> tuple:
        success = False
        outcome_msg = ""
        should_update_dashboard = False
        assigned_room = None

        async with await DatabaseManager.get_connection() as conn:
            # 1. Validação Multi-Contas por mapa
            active = await conn.fetchrow(
                "SELECT * FROM claims WHERE guild_id = $1 AND map_type = $2 AND user_id = $3 AND status = 'ACTIVE'",
                guild_id, map_type, user.id
            )
            if active:
                return False, f"❌ **Falhou!** Você já possui uma sala ativa em **{map_type.replace('_', ' ')}**!"

            # 2. Busca dados do spot
            spot_info = Config.MAP_DATA[map_type]["floors"][floor][spot_type]
            max_rooms = spot_info.get("rooms", 1)

            # 3. Busca ocupação atual deste spot
            rows = await conn.fetch("""
                SELECT room_number, status, ends_at, id FROM claims
                WHERE guild_id = $1 AND map_type = $2 AND floor = $3 AND spot_type = $4 AND status IN ('ACTIVE', 'VACANT_REMAINING')
            """, guild_id, map_type, floor, spot_type)
            
            occupied_rooms = {r["room_number"]: r for r in rows}

            # Cenário A: Se houver algum quarto completamente livre, aloca nele direto
            for r in range(1, max_rooms + 1):
                if r not in occupied_rooms:
                    assigned_room = r
                    break

            if assigned_room is not None:
                # Cria a claim normalmente no quarto alocado automaticamente
                now = datetime.utcnow()
                ends = now + timedelta(minutes=tickets * 30)
                await conn.execute("""
                    INSERT INTO claims (guild_id, map_type, floor, spot_type, room_number, status, user_id, username, started_at, ends_at, tickets)
                    VALUES ($1, $2, $3, $4, $5, 'ACTIVE', $6, $7, $8, $9, $10)
                """, guild_id, map_type, floor, spot_type, assigned_room, user.id, user.display_name, now, ends, tickets)
                
                success = True
                outcome_msg = f"✅ **Sucesso!** Spot `{floor} - {spot_type}` (Sala {assigned_room}) reservado."
                should_update_dashboard = True

            else:
                # Cenário B: Se todos estiverem ocupados, tenta achar um "Tempo Restante" (VACANT_REMAINING)
                vacant_rooms = [dict(r) for r in rows if r["status"] == "VACANT_REMAINING"]
                if vacant_rooms:
                    # Aloca no quarto com o MENOR TEMPO restante (ends_at mais próximo)
                    vacant_rooms.sort(key=lambda x: x["ends_at"])
                    target_claim = vacant_rooms[0] # EXTRAÇÃO DO PRIMEIRO ELEMENTO DA LISTA DE FORMA SEGURA ✅
                    assigned_room = target_claim["room_number"]
                    
                    # Consome o tempo restante
                    await conn.execute(
                        "UPDATE claims SET status = 'ACTIVE', user_id = $1, username = $2 WHERE id = $3",
                        user.id, user.display_name, target_claim["id"]
                    )
                    
                    success = True
                    outcome_msg = f"✅ **Sucesso!** Você assumiu o tempo restante de `{floor} - {spot_type}` (Sala {assigned_room})."
                    should_update_dashboard = True
                    
                else:
                    # Cenário C: Todos os quartos ativos por outros jogadores. Entra na fila.
                    if spot_info.get("allow_queue", True):
                        q_size = await conn.fetchval(
                            "SELECT COUNT(*) FROM spot_queues WHERE guild_id = $1 AND map_type = $2 AND floor = $3 AND spot_type = $4",
                            guild_id, map_type, floor, spot_type
                        ) or 0
                        
                        if q_size >= Config.MAX_QUEUE_SIZE:
                            return False, f"❌ **Fila Cheia!** O limite de {Config.MAX_QUEUE_SIZE} pessoas na fila foi atingido."

                        await conn.execute("""
                            INSERT INTO spot_queues (guild_id, map_type, floor, spot_type, user_id, username, tickets)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """, guild_id, map_type, floor, spot_type, user.id, user.display_name, tickets)
                        
                        success = True
                        outcome_msg = f"👥 **Fila de Espera!** Você entrou na fila para o spot **{spot_type}**."
                        should_update_dashboard = True
                    else:
                        success = False
                        outcome_msg = "❌ **Ocupado!** Fila de espera desabilitada para eventos rápidos Frenzy/Fury."

        # Executa as ações de atualização e logs de auditoria fora do bloco de conexão para EVITAR DEADLOCKS NO POSTGRES! ✅
        if should_update_dashboard:
            try:
                await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
                if success and assigned_room is not None:
                    if outcome_msg.startswith("✅ **Sucesso!** Spot"):
                        await self.log_service.dispatch_claim_log(guild_id, user, map_type, floor, spot_type, assigned_room, "CLAIM", f"Tickets: {tickets} ({tickets * 30}m)")
                    else:
                        await self.log_service.dispatch_claim_log(guild_id, user, map_type, floor, spot_type, assigned_room, "CLAIM_VACANT", "Assumiu tempo restante")
            except Exception as e:
                logger.error(f"Erro ao pós-processar dashboard/logs de claim: {e}")

        return success, outcome_msg

    async def release_claim(self, guild_id: int, user: discord.User, map_type: str) -> str:
        floor = None
        spot_type = None
        room_number = None
        msg = ""
        should_update_dashboard = False

        async with await DatabaseManager.get_connection() as conn:
            claim = await conn.fetchrow(
                "SELECT * FROM claims WHERE guild_id = $1 AND map_type = $2 AND user_id = $3 AND status = 'ACTIVE'",
                guild_id, map_type, user.id
            )

            if not claim:
                in_q = await conn.fetchrow(
                    "SELECT * FROM spot_queues WHERE guild_id = $1 AND map_type = $2 AND user_id = $3",
                    guild_id, map_type, user.id
                )
                if in_q:
                    await conn.execute("DELETE FROM spot_queues WHERE id = $1", in_q["id"])
                    floor = in_q["floor"]
                    should_update_dashboard = True
                    msg = f"✅ Você saiu da fila de espera do spot **{in_q['spot_type']}**."
                else:
                    msg = "⚠️ Você não possui claims ativos ou posições em filas."
            else:
                floor = claim["floor"]
                spot_type = claim["spot_type"]
                room_number = claim["room_number"]
                should_update_dashboard = True

                queue_list = await self.get_queue_list(map_type, floor, spot_type)
                if queue_list:
                    await conn.execute("UPDATE claims SET status = 'VACANT_REMAINING' WHERE id = $1", claim["id"])
                    msg = f"✅ Você liberou o spot **{spot_type}**. Ele virou **Tempo Restante** no placar!"
                else:
                    await conn.execute("UPDATE claims SET status = 'CANCELLED' WHERE id = $1", claim["id"])
                    msg = f"✅ Você desocupou o spot **{spot_type}**!"

        # Atualizações de dashboard fora do bloco de conexão ativa para evitar saturação do pool ✅
        if should_update_dashboard and floor:
            try:
                await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
                if room_number is not None:
                    await self.log_service.dispatch_claim_log(guild_id, user, map_type, floor, spot_type, room_number, "RELEASE")
            except Exception as e:
                logger.error(f"Erro ao pós-processar cancelamento de claim: {e}")

        return msg

    async def trigger_floor_event(self, guild_id: int, user: discord.User, map_type: str, floor: str, event_key: str) -> tuple:
        async with await DatabaseManager.get_connection() as conn:
            boss_owner = await conn.fetchrow(
                "SELECT * FROM claims WHERE guild_id = $1 AND map_type = $2 AND floor = $3 AND spot_type = 'BOSS' AND status = 'ACTIVE'",
                guild_id, map_type, floor
            )

            if boss_owner and boss_owner["user_id"] != user.id:
                return False, f"⚠️ **Acesso Negado!** Somente o dono legítimo do BOSS (<@{boss_owner['user_id']}>) pode gerenciar as rotações deste andar."

            now = datetime.utcnow()
            await conn.execute("""
                INSERT INTO floor_events (guild_id, map_type, floor, event_name, last_triggered_at, last_triggered_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT(guild_id, map_type, floor, event_name) DO UPDATE SET
                    last_triggered_at = EXCLUDED.last_triggered_at,
                    last_triggered_by = EXCLUDED.last_triggered_by;
            """, guild_id, map_type, floor, event_key, now, user.id)

        # Atualização fora do bloco de conexão ativa ✅
        try:
            await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
        except Exception as e:
            logger.error(f"Erro ao pós-processar atualização de evento de respawn: {e}")

        return True, f"✅ Rotação de **{event_key}** atualizada para as {now.strftime('%H:%M')}!"
