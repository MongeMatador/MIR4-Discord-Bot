import discord
from typing import List, Dict
from datetime import datetime

class MIR4Embeds:
    """Sleek, static, high-performance instructional embeds for MIR4 Bot."""

    @staticmethod
    def build_panel_embed(claims: List[Dict] = None) -> discord.Embed:
        # Mantemos o painel de claims limpo, estático e elegante sem misturar os mapas.
        # Todas as salas e andares ocupados são mostrados individualmente nos seus canais específicos.
        embed = discord.Embed(
            title="⚔️ CLAN OPERATIONAL DASHBOARD | PAINEL DE CLAIMS ⚔️",
            description=(
                "🇺🇸 **How to claim a spot?**\n"
                "• Click on **Claim Spot** below;\n"
                "• Select your Map, Floor, Spot, Room, and Tickets.\n\n"
                "🇧🇷 **Como reservar um spot?**\n"
                "• Clique em **Claim Spot** abaixo;\n"
                "• Selecione o Mapa, Andar, Spot, Sala e Tickets.\n\n"
                "🇪🇸 **¿Cómo solicitar uma ubicación?**\n"
                "• Oprima en **Claim Spot** abajo;\n"
                "• Seleccione el Mapa, Piso, Spot, Sala y Tickets."
            ),
            color=discord.Color.gold(),
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
