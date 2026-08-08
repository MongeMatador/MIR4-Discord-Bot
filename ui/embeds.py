import discord
from typing import List, Dict
from datetime import datetime

class MIR4Embeds:
    @staticmethod
    def build_panel_embed(claims: List[Dict]) -> discord.Embed:
        embed = discord.Embed(
            title="⚔️ PAINEL DE CONTROLE DE SPOTS - MIR4 ⚔️",
            description="Utilize os botões abaixo para **Reivindicar (Claim)** ou **Liberar** seu spot na Praça / Pico Secreto.\n\n"
                        "*(Painel sincronizado em tempo real)*",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )

        available_spots = [
            "Praça 1 - Ouro", "Praça 2 - Pedra de Alma", "Praça 3 - Ervas",
            "Pico 1 - Minério", "Pico 2 - Boss", "Pico 3 - Essência"
        ]

        claims_map = {c["spot_name"]: c for c in claims}

        for spot in available_spots:
            if spot in claims_map:
                c = claims_map[spot]
                status = f"🔴 **Ocupado por:** <@{c['user_id']}>\n⏱️ Em: `{c['claimed_at']}`"
            else:
                status = "🟢 **LIVRE**"

            embed.add_field(name=f"📍 {spot}", value=status, inline=True)

        embed.set_footer(text="MIR4 Clan Management • Render Active")
        return embed
