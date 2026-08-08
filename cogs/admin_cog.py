import discord
from discord.ext import commands
from discord import app_commands

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="limpar_claims", description="[Admin] Limpa todos os claims ativos do servidor.")
    @commands.has_permissions(administrator=True)
    async def limpar_claims(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.claim_repo.clear_all_claims(interaction.guild_id)
        await self.bot.panel_service.update_panel(interaction.guild_id)
        await interaction.followup.send("🧹 Todos os claims foram limpos!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
