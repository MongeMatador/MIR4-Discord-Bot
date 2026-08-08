import discord
from discord.ext import commands
from discord import app_commands

class ClaimCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_painel", description="Inicializa o Painel Único do MIR4 no canal atual.")
    @commands.has_permissions(administrator=True)
    async def setup_painel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.panel_service.update_panel(
            guild_id=interaction.guild_id, 
            target_channel=interaction.channel
        )
        await interaction.followup.send("✅ Painel configurado com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClaimCog(bot))
