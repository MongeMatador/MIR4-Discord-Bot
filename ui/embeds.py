import discord
from typing import List, Dict
from datetime import datetime
from config import Config

class MIR4Embeds:
    """Sleek, static, high-performance instructional embeds for MIR4 Bot."""

    @staticmethod
    def build_panel_embed(map_type: str) -> discord.Embed:
        if map_type == "MAGIC_SQUARE":
            title = "🔮 PAINEL DE CLAIMS - PRAÇA MÁGICA 🔮"
            color = discord.Color.purple()
            description = (
                "🇺🇸 **How to claim a spot?**\n"
                "• Click on **Claim Spot** below;\n"
                "• Select your Floor, Spot, Room, and Tickets.\n\n"
                "🇧🇷 **Como reservar um spot?**\n"
                "• Clique em **Claim Spot** abaixo;\n"
                "• Selecione o Andar, Spot, Sala e Tickets.\n\n"
                "🇪🇸 **¿Cómo solicitar una ubicación?**\n"
                "• Oprima en **Claim Spot** abajo;\n"
                "• Seleccione el Piso, Spot, Sala y Tickets."
            )
        else:
            title = "🏔️ PAINEL DE CLAIMS - PICO SECRETO 🏔️"
            color = discord.Color.orange()
            description = (
                "🇺🇸 **How to claim a spot?**\n"
                "• Click on **Claim Spot** below;\n"
                "• Select your Floor, Spot, and Tickets.\n\n"
                "🇧🇷 **Como reservar um spot?**\n"
                "• Clique em **Claim Spot** abaixo;\n"
                "• Selecione o Andar, Spot e Tickets.\n\n"
                "🇪🇸 **¿Cómo solicitar una ubicación?**\n"
                "• Oprima en **Claim Spot** abajo;\n"
                "• Seleccione el Piso, Spot y Tickets."
            )

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📌 IMPORTANT INFORMATION / INFORMAÇÕES IMPORTANTES",
            value=(
                "• 🇺🇸 **Real-time boards:** Active claims are shown in each specific floor channel.\n"
                "• 🇧🇷 **Placares em tempo real:** As salas ocupadas aparecem nos canais específicos de cada andar.\n"
                "• 🇪🇸 **Tableros en tiempo real:** Las salas ocupadas se muestran en los canales específicos de cada piso."
            ),
            inline=False
        )

        embed.set_footer(text="MIR4 Clan Management • Render Active")
        return embed

    @staticmethod
    def build_floor_embed(map_type: str, floor_key: str, claims: List[Dict]) -> discord.Embed:
        map_label = "Magic Square" if map_type == "MAGIC_SQUARE" else "Secret Peak"
        map_emoji = "🔮" if map_type == "MAGIC_SQUARE" else "🏔️"
        
        embed = discord.Embed(
            title=f"{map_emoji} {map_label.upper()} - {floor_key} ⚔️",
            description="Real-time monitoring scoreboard / Placar de monitoramento em tempo real",
            color=discord.Color.purple() if map_type == "MAGIC_SQUARE" else discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        spots = Config.MAP_DATA[map_type]["floors"].get(floor_key, {})
        
        # Filtra os claims ativos deste andar específico
        floor_claims = []
        for c in claims:
            if map_label in c["spot_name"] and floor_key in c["spot_name"]:
                floor_claims.append(c)

        for spot_name, info in spots.items():
            max_rooms = info.get("rooms", 1)
            emoji = info.get("emoji", "📍")
            
            field_value = ""
            for room in range(1, max_rooms + 1):
                found_claim = None
                for fc in floor_claims:
                    if f"- {spot_name} - Room {room}" in fc["spot_name"]:
                        found_claim = fc
                        break
                
                if found_claim:
                    field_value += f"🔴 **Room {room}**: {found_claim['user_name']} (Occupied)\n"
                else:
                    field_value += f"🟢 **Room {room}**: Livre / Available\n"
            
            embed.add_field(
                name=f"{emoji} {spot_name}",
                value=field_value,
                inline=True
            )
            
        embed.set_footer(text="MIR4 Real-Time Tracker • Updated")
        return embed
