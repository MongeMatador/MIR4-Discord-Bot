import discord
from typing import List, Dict
from datetime import datetime

class MIR4Embeds:
    """Sleek, static, high-performance instructional embeds for MIR4 Bot."""

    @staticmethod
    def build_panel_embed(map_type: str, claims: List[Dict] = None) -> discord.Embed:
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
                "🇪🇸 **¿Cómo solicitar uma ubicación?**\n"
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
                "🇪🇸 **¿Cómo solicitar uma ubicación?**\n"
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
                "• 🇪🇸 **Tableros en tempo real:** Las salas ocupadas se muestran em los canales específicos de cada piso."
            ),
            inline=False
        )

        embed.set_footer(text="MIR4 Clan Management • Render Active")
        return embed
