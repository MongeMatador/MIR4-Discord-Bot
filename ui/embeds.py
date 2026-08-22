import discord
from typing import List, Dict
from datetime import datetime, timedelta
from config import Config

class MIR4Embeds:
    @staticmethod
    def parse_datetime(val) -> datetime:
        """Helper para analisar datas com segurança (suporta tanto strings quanto datetimes nativos)."""
        if val is None:
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val)
            except ValueError:
                # Fallback para possíveis formatações com sufixo Z do javascript/API
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
        return val

    @staticmethod
    def build_panel_embed(map_type: str) -> discord.Embed:
        if map_type == "MAGIC_SQUARE":
            title = "🔮 PAINEL DE CLAIMS - PRAÇA MÁGICA 🔮"
            color = discord.Color.purple()
            desc = (
                "🇺🇸 **How to claim a spot?**\n• Click on **Claim Spot** below;\n• Select your Floor, Spot, and Tickets.\n\n"
                "🇧🇷 **Como reservar um spot?**\n• Clique em **Claim Spot** abaixo;\n• Selecione o Andar, Spot e Tickets.\n\n"
                "🇪🇸 **¿Cómo solicitar una ubicación?**\n• Oprima en **Claim Spot** abaixo;\n• Seleccione el Piso, Spot y Tickets."
            )
        else:
            title = "🏔️ PAINEL DE CLAIMS - PICO SECRETO 🏔️"
            color = discord.Color.orange()
            desc = (
                "🇺🇸 **How to claim a spot?**\n• Click on **Claim Spot** below;\n• Select your Floor, Spot, and Tickets.\n\n"
                "🇧🇷 **Como reservar um spot?**\n• Clique em **Claim Spot** abaixo;\n• Selecione o Andar, Spot e Tickets.\n\n"
                "🇪🇸 **¿Cómo solicitar una ubicación?**\n• Oprima en **Claim Spot** abaixo;\n• Seleccione el Piso, Spot y Tickets."
            )
        
        embed = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.utcnow())
        embed.add_field(
            name="📌 IMPORTANT INFORMATION / INFORMAÇÕES IMPORTANTES",
            value="• Active claims are shown in each specific floor channel.\n• As salas ocupadas aparecem nos canais específicos de cada andar.",
            inline=False
        )
        
        # MANTIDO ESTREITAMENTE NO PAINEL DE CLIQUE DO CANAL DE CLAIMS PRINCIPAL! ✅
        if map_type == "SECRET_PEAK" and getattr(Config, "SECRET_PEAK_MAP_URL", None):
            embed.set_image(url=Config.SECRET_PEAK_MAP_URL)
            
        embed.set_footer(text="MIR4 Clan Management")
        return embed

    @staticmethod
    def build_floor_embed(map_type: str, floor_key: str, claims: List[Dict], events_map: Dict, ticker_line: str, queues: List[Dict] = None) -> discord.Embed:
        map_label = "Magic Square" if map_type == "MAGIC_SQUARE" else "Secret Peak"
        map_emoji = "🔮" if map_type == "MAGIC_SQUARE" else "🏔️"
        color = discord.Color.purple() if map_type == "MAGIC_SQUARE" else discord.Color.orange()

        embed = discord.Embed(
            title=f"{map_emoji} {map_label.upper()} - {floor_key} ⚔️",
            color=color,
            timestamp=datetime.utcnow()
        )

        if ticker_line:
            embed.add_field(name="📊 LIVE STATUS TAPE", value=ticker_line, inline=False)

        valid_events = Config.get_valid_events_for_floor(map_type, floor_key)
        activity_lines = []
        for evt_key in valid_events:
            evt_config = Config.TRACKABLE_EVENTS[map_type][evt_key]
            last_triggered_at = events_map.get(evt_key)
            if last_triggered_at:
                dt_trigger_raw = MIR4Embeds.parse_datetime(last_triggered_at)
                dt_trigger = dt_trigger_raw + timedelta(hours=Config.TIMEZONE_OFFSET)
                time_display = f"**{dt_trigger.strftime('%H:%M')}**"
            else:
                time_display = "--:--"
            activity_lines.append(f"{evt_config['emoji']} **{evt_config['label']}:** {time_display}")

        if activity_lines:
            embed.add_field(name="📋 Horários de Respawn / Rotação", value="\n".join(activity_lines), inline=False)

        embed.add_field(name="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", value="**🛡️ MONITORAMENTO DE RECURSOS ATIVOS**", inline=False)

        spots = Config.MAP_DATA[map_type]["floors"].get(floor_key, {})
        for spot_name, info in spots.items():
            max_rooms = info.get("rooms", 1)
            emoji = info.get("emoji", "📍")
            
            spot_claims = [c for c in claims if c["spot_type"] == spot_name]
            claims_by_room = {c["room_number"]: c for c in spot_claims}
            
            field_value = ""
            for r in range(1, max_rooms + 1):
                room_text = f"🔹 Sala {r}: " if max_rooms > 1 else ""
                if r in claims_by_room:
                    c = claims_by_room[r]
                    
                    ends_at_dt = MIR4Embeds.parse_datetime(c["ends_at"])
                    started_at_dt = MIR4Embeds.parse_datetime(c["started_at"])
                    
                    end_time_server = ends_at_dt + timedelta(hours=Config.TIMEZONE_OFFSET)
                    
                    if c["status"] == "VACANT_REMAINING":
                        field_value += f"{room_text}🟢 **Tempo Restante** | Até {end_time_server.strftime('%H:%M')}\n"
                    else:
                        start_time_server = started_at_dt + timedelta(hours=Config.TIMEZONE_OFFSET)
                        field_value += f"{room_text}🔴 <@{c['user_id']}> ({start_time_server.strftime('%H:%M')} ~ {end_time_server.strftime('%H:%M')})\n"
                else:
                    field_value += f"{room_text}🟢 Disponível\n"

            # EXIBIÇÃO DA FILA DE ESPERA SE HOUVER ✅
            if queues:
                spot_queues = [q for q in queues if q["spot_type"] == spot_name]
                if spot_queues:
                    queue_lines = []
                    for idx, q in enumerate(spot_queues):
                        queue_lines.append(f"⏱️ **{idx+1}º** <@{q['user_id']}> ({q['tickets'] * 30}m)")
                    field_value += "👥 **Fila de Espera:**\n" + "\n".join(queue_lines) + "\n"

            # GRID SEGURO DE 3 COLUNAS LADO A LADO ✅
            if map_type == "SECRET_PEAK":
                use_inline = spot_name in ["A1", "A2", "N1", "N2", "S1", "S2"]
            else:  # MAGIC_SQUARE
                use_inline = spot_name in ["ADC1", "ADC2", "ADC3"]

            embed.add_field(name=f"{emoji} {spot_name}", value=field_value, inline=use_inline)

        embed.set_footer(text="MIR4 Real-Time Tracker")
        return embed
📄 4. services/claim_service.py
(Força a liberação rápida de conexões com o banco Supabase, fechando-as imediatamente antes de redesenhar os canais do Discord para evitar deadlocks)
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
        action_type = None  # "CLAIM", "CLAIM_VACANT", "QUEUE", "FAILED"
        assigned_room = None
        error_msg = None
        log_msg = None
        target_claim_id = None

        async with await DatabaseManager.get_connection() as conn:
            # 1. Validação Multi-Contas por mapa
            active = await conn.fetchrow(
                "SELECT * FROM claims WHERE guild_id = $1 AND map_type = $2 AND user_id = $3 AND status = 'ACTIVE'",
                guild_id, map_type, user.id
            )
            if active:
                return False, f"❌ **Falhou!** Você já possui uma sala ativa em **{map_type.replace('_', ' ')}**!"

            # Busca dados do spot
            spot_info = Config.MAP_DATA[map_type]["floors"][floor][spot_type]
            max_rooms = spot_info.get("rooms", 1)

            # Busca ocupação atual deste spot
            rows = await conn.fetch("""
                SELECT room_number, status, ends_at, id FROM claims
                WHERE guild_id = $1 AND map_type = $2 AND floor = $3 AND spot_type = $4 AND status IN ('ACTIVE', 'VACANT_REMAINING')
            """, guild_id, map_type, floor, spot_type)
            
            occupied_rooms = {r["room_number"]: r for r in rows}

            # Cenário A: Se houver algum quarto livre, aloca diretamente nele
            for r in range(1, max_rooms + 1):
                if r not in occupied_rooms:
                    assigned_room = r
                    break

            # Cenário B: Se todos ocupados, tenta achar "Tempo Restante" (VACANT_REMAINING)
            if assigned_room is None:
                vacant_rooms = [dict(r) for r in rows if r["status"] == "VACANT_REMAINING"]
                if vacant_rooms:
                    vacant_rooms.sort(key=lambda x: x["ends_at"])
                    target_claim = vacant_rooms[0]
                    assigned_room = target_claim["room_number"]
                    target_claim_id = target_claim["id"]
                    action_type = "CLAIM_VACANT"

                    # Atualiza o status da claim restante para ativo para este usuário
                    await conn.execute(
                        "UPDATE claims SET status = 'ACTIVE', user_id = $1, username = $2 WHERE id = $3",
                        user.id, user.display_name, target_claim_id
                    )

            # Cenário C: Todos ocupados e sem tempo restante. Entra na fila.
            if assigned_room is None:
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
                    action_type = "QUEUE"
                else:
                    return False, "❌ **Ocupado!** Fila de espera desabilitada para eventos rápidos Frenzy/Fury."

            # Cenário A (Criação de nova claim ativa em quarto vago)
            if assigned_room is not None and action_type is None:
                now = datetime.utcnow()
                ends = now + timedelta(minutes=tickets * 30)
                await conn.execute("""
                    INSERT INTO claims (guild_id, map_type, floor, spot_type, room_number, status, user_id, username, started_at, ends_at, tickets)
                    VALUES ($1, $2, $3, $4, $5, 'ACTIVE', $6, $7, $8, $9, $10)
                """, guild_id, map_type, floor, spot_type, assigned_room, user.id, user.display_name, now, ends, tickets)
                action_type = "CLAIM"

        # --- FORA DO CONTEXTO DE CONEXÃO: ATUALIZAÇÕES VISUAIS E LOGS ---
        if action_type == "CLAIM_VACANT":
            await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
            await self.log_service.dispatch_claim_log(guild_id, user, map_type, floor, spot_type, assigned_room, "CLAIM_VACANT", "Assumiu tempo restante")
            return True, f"✅ **Sucesso!** Você assumiu o tempo restante de `{floor} - {spot_type}` (Sala {assigned_room})."
        
        elif action_type == "QUEUE":
            await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
            return True, f"👥 **Fila de Espera!** Você entrou na fila para o spot **{spot_type}**."
        
        elif action_type == "CLAIM":
            await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
            await self.log_service.dispatch_claim_log(guild_id, user, map_type, floor, spot_type, assigned_room, "CLAIM", f"Tickets: {tickets} ({tickets * 30}m)")
            return True, f"✅ **Sucesso!** Spot `{floor} - {spot_type}` (Sala {assigned_room}) reservado."

        return False, "❌ Ocorreu um erro desconhecido ao processar sua solicitação."

    async def release_claim(self, guild_id: int, user: discord.User, map_type: str) -> str:
        action_type = None  # "RELEASE_QUEUE", "RELEASE_VACANT", "RELEASE_CANCELLED", "NONE"
        floor = None
        spot_type = None
        room_number = None
        outcome_msg = ""

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
                    spot_type = in_q["spot_type"]
                    action_type = "RELEASE_QUEUE"
                    outcome_msg = f"✅ Você saiu da fila de espera do spot **{spot_type}**."
                else:
                    return "⚠️ Você não possui claims ativos ou posições em filas."
            else:
                floor = claim["floor"]
                spot_type = claim["spot_type"]
                room_number = claim["room_number"]

                # Verifica se há alguém na fila para herdar como tempo restante
                rows = await conn.fetch("""
                    SELECT * FROM spot_queues WHERE guild_id = $1 AND map_type = $2 AND floor = $3 AND spot_type = $4 ORDER BY queued_at ASC
                """, guild_id, map_type, floor, spot_type)
                queue_list = [dict(r) for r in rows]

                if queue_list:
                    await conn.execute("UPDATE claims SET status = 'VACANT_REMAINING' WHERE id = $1", claim["id"])
                    action_type = "RELEASE_VACANT"
                    outcome_msg = f"✅ Você liberou o spot **{spot_type}**. Ele virou **Tempo Restante** no placar!"
                else:
                    await conn.execute("UPDATE claims SET status = 'CANCELLED' WHERE id = $1", claim["id"])
                    action_type = "RELEASE_CANCELLED"
                    outcome_msg = f"✅ Você desocupou o spot **{spot_type}**!"

        # --- FORA DO CONTEXTO DE CONEXÃO: ATUALIZAÇÕES VISUAIS E LOGS ---
        if action_type in ["RELEASE_QUEUE", "RELEASE_VACANT", "RELEASE_CANCELLED"]:
            await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)
            if action_type != "RELEASE_QUEUE":
                await self.log_service.dispatch_claim_log(guild_id, user, map_type, floor, spot_type, room_number, "RELEASE")
        
        return outcome_msg

    async def trigger_floor_event(self, guild_id: int, user: discord.User, map_type: str, floor: str, event_key: str) -> tuple:
        success = False
        outcome_msg = ""

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
            success = True
            outcome_msg = f"✅ Rotação de **{event_key}** atualizada para as {now.strftime('%H:%M')}!"

        # --- FORA DO CONTEXTO DE CONEXÃO: ATUALIZAÇÕES VISUAIS ---
        if success:
            await self.panel_service.update_floor_dashboard(guild_id, map_type, floor)

        return success, outcome_msg
