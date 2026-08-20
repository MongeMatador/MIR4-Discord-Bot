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
    def build_floor_embed(map_type: str, floor_key: str, claims: List[Dict], events_map: Dict, ticker_line: str) -> discord.Embed:
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

            embed.add_field(name=f"{emoji} {spot_name}", value=field_value, inline=False)

        # 🚀 AQUI ESTÁ A CORREÇÃO SOLICITADA: embed.set_image(...) FOI TOTALMENTE REMOVIDO DA SALA/PLACAR! ✅
        # Dessa forma, os canais de andares ficam curtos e minimalistas, sem repetição de imagens!

        embed.set_footer(text="MIR4 Real-Time Tracker")
        return embed
