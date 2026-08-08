import discord
from discord.ext import commands
from discord import app_commands
from database.repositories.log_repository import LogRepository
from utils.logger import log

class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_repo = LogRepository()

    @app_commands.command(name="set_log_channel", description="Configura o canal de logs para Praça e Pico Secreto.")
    @app_commands.describe(
        categoria="Categoria de logs",
        canal="Canal de texto onde os logs serão enviados"
    )
    @commands.has_permissions(administrator=True)
    async def set_log_channel(
        self,
        interaction: discord.Interaction,
        categoria: str,
        canal: discord.TextChannel
    ):
        await interaction.response.defer(ephemeral=True)

        success = await self.log_repo.set_log_channel(interaction.guild_id, categoria, canal.id)

        if success:
            embed = discord.Embed(
                title="✅ Canal de Logs Configurado",
                description=f"Os logs da categoria **{categoria.upper()}** agora serão enviados em {canal.mention}.",
                color=discord.Color.brand_green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Teste imediato no canal de logs
            test_embed = discord.Embed(
                title="🔔 Teste de Integração de Logs",
                description="O sistema de logs de Praça e Pico do MIR4 foi ativado neste canal com sucesso!",
                color=discord.Color.blue()
            )
            try:
                await canal.send(embed=test_embed)
            except Exception as e:
                log.warning(f"Não foi possível enviar mensagem de teste em {canal.id}: {e}")
        else:
            await interaction.followup.send("❌ Erro ao salvar configuração no banco de dados.", ephemeral=True)

    @set_log_channel.autocomplete('categoria')
    async def category_autocomplete(self, interaction: discord.Interaction, current: str):
        categories = ["MAGIC_SQUARE", "SECRET_PEAK", "CLAIMS", "GERAL"]
        return [
            app_commands.Choice(name=cat, value=cat)
            for cat in categories if current.lower() in cat.lower()
        ]

async def setup(bot):
    await bot.add_cog(LogsCog(bot))
