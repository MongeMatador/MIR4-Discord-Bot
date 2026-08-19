import discord
from discord.ext import commands
from discord import app_commands
from database.connection import DatabaseManager

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="limpar_claims", description="[Admin] Limpa todos os claims ativos do servidor.")
    @app_commands.checks.has_permissions(administrator=True) # CORRIGIDO ✅
    async def limpar_claims(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with await DatabaseManager.get_connection() as conn:
            await conn.execute("DELETE FROM claims")
            await conn.execute("DELETE FROM spot_queues")
        await interaction.followup.send("🧹 Todos os claims e filas foram limpos com sucesso!", ephemeral=True)

    # Tratador de erro amigável para falta de permissão
    @limpar_claims.error
    async def limpar_claims_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ Você não tem permissão de Administrador para usar este comando!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
