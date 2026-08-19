import discord
from discord.ext import commands
from discord import app_commands
from database.connection import DatabaseManager

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="limpar_claims", description="[Admin] Limpa todos os claims ativos do servidor.")
    @commands.has_permissions(administrator=True)
    async def limpar_claims(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with DatabaseManager.get_connection() as db:
            await db.execute("DELETE FROM claims")
            await db.execute("DELETE FROM spot_queues")
            await db.commit()
        await interaction.followup.send("🧹 Todos os claims e filas foram limpos com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
