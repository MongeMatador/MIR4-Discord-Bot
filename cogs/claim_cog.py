import discord
from discord.ext import commands
from discord import app_commands

class ClaimCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setup_painel",
        description="Inicializa o painel de claims para a Praça Mágica ou Pico Secreto."
    )
    @app_commands.describe(map_type="Selecione o mapa para este painel")
    @app_commands.choices(map_type=[
        app_commands.Choice(name="🔮 Praça Mágica", value="MAGIC_SQUARE"),
        app_commands.Choice(name="🏔️ Pico Secreto", value="SECRET_PEAK")
    ])
    @commands.has_permissions(administrator=True)
    async def setup_painel(self, interaction: discord.Interaction, map_type: str):
        # DEFER IMEDIATO PARA EVITAR TIMEOUTS
        await interaction.response.defer(ephemeral=True)
        await self.bot.panel_service.update_panel(
            guild_id=interaction.guild_id,
            map_type=map_type,
            target_channel=interaction.channel
        )
        lbl = "Praça Mágica" if map_type == "MAGIC_SQUARE" else "Pico Secreto"
        await interaction.followup.send(f"✅ Painel de claims de **{lbl}** operando e sincronizado!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClaimCog(bot))
