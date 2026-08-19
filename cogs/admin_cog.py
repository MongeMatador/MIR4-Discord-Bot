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
        async with await DatabaseManager.get_connection() as conn:
            await conn.execute("DELETE FROM claims")
            await conn.execute("DELETE FROM spot_queues")
        await interaction.followup.send("🧹 Todos os claims e filas foram limpos com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
📄 8. cogs/logs_cog.py
(Vinculador e persistente do cadastro de canais de auditoria no PostgreSQL)
import discord
from discord.ext import commands
from discord import app_commands
from database.connection import DatabaseManager

class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_log_channel", description="Configura o canal de logs para Praça e Pico Secreto.")
    @app_commands.describe(
        categoria="Categoria de logs (mapa correspondente)",
        canal="Canal de texto de destino"
    )
    @app_commands.choices(
        categoria=[
            app_commands.Choice(name="🔮 Praça Mágica", value="MAGIC_SQUARE"),
            app_commands.Choice(name="🏔️ Pico Secreto", value="SECRET_PEAK")
        ]
    )
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, interaction: discord.Interaction, categoria: str, canal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        async with await DatabaseManager.get_connection() as conn:
            await conn.execute("""
                INSERT INTO guild_log_channels (guild_id, category, channel_id, updated_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT(guild_id, category) DO UPDATE SET channel_id = EXCLUDED.channel_id, updated_at = CURRENT_TIMESTAMP;
            """, interaction.guild_id, categoria.upper(), canal.id)

        embed = discord.Embed(
            title="✅ Canal de Logs Configurado",
            description=f"Os logs de auditoria de **{categoria}** serão entregues em {canal.mention}.",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(LogsCog(bot))
