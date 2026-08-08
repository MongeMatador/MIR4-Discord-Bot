import discord
from typing import List, Dict
from datetime import datetime

class MIR4Embeds:
    """Industrial-grade dynamic Embed constructor for MIR4 Discord Bot."""

    @staticmethod
    def build_panel_embed(claims: List[Dict]) -> discord.Embed:
        embed = discord.Embed(
            title="⚔️ CLAN OPERATIONAL DASHBOARD | PAINEL DE CLAIMS ⚔️",
            description="🇺🇸 **How to claim?** Click **Claim Spot** below, select floor, spot, room, and tickets.\n"
                        "🇧🇷 **Como claimar?** Clique em **Claim Spot** abaixo, selecione o andar, spot, sala e tickets.\n"
                        "🇪🇸 **¿Cómo solicitar?** Oprima **Claim Spot**, seleccione piso, spot, sala y tiempo.",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )

        # Categorizes claims dynamically
        ms_claims = []
        sp_claims = []

        for c in claims:
            spot_name = c.get("spot_name", "")
            # Supports both English and Portuguese/Spanish naming patterns
            if "Magic Square" in spot_name or "Praça" in spot_name:
                ms_claims.append(c)
            elif "Secret Peak" in spot_name or "Pico" in spot_name:
                sp_claims.append(c)
            else:
                ms_claims.append(c)

        # 🔮 MAGIC SQUARE SECTION
        if ms_claims:
            ms_text = ""
            for c in ms_claims:
                # Cleans up the string prefix for a sleek look
                clean_spot = c["spot_name"].replace("Magic Square ", "").replace("Praça ", "")
                ms_text += f"🔴 **{clean_spot}**\n└ Occupied by: <@{c['user_id']}> | `⏱️ {c['claimed_at']}`\n\n"
            embed.add_field(name="🔮 MAGIC SQUARE ACTIVE CLAIMS", value=ms_text, inline=False)
        else:
            embed.add_field(
                name="🔮 MAGIC SQUARE", 
                value="🟢 **All chambers are vacant / Todos os spots estão livres**", 
                inline=False
            )

        # 🏔️ SECRET PEAK SECTION
        if sp_claims:
            sp_text = ""
            for c in sp_claims:
                clean_spot = c["spot_name"].replace("Secret Peak ", "").replace("Pico ", "")
                sp_text += f"🔴 **{clean_spot}**\n└ Occupied by: <@{c['user_id']}> | `⏱️ {c['claimed_at']}`\n\n"
            embed.add_field(name="🏔️ SECRET PEAK ACTIVE CLAIMS", value=sp_text, inline=False)
        else:
            embed.add_field(
                name="🏔️ SECRET PEAK", 
                value="🟢 **All chambers are vacant / Todos os spots estão livres**", 
                inline=False
            )

        embed.set_footer(text="MIR4 Clan Management • Render High-Availability Active")
        return embed
