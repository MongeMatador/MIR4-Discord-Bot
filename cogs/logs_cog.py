import discord
from discord.ext import commands
from discord import app_commands

class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_log_channel", description="Configura o canal de logs para Praça e Pico Secreto.")
    @app_commands.describe(
        categoria="Categoria de logs",
        canal="Canal de texto de destino"
    )
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, interaction: discord.Interaction, categoria: str, canal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        success = await self.bot.log_repo.set_log_channel(interaction.guild_id, categoria, canal.id)

        if success:
            embed = discord.Embed(
                title="✅ Canal de Logs Configurado",
                description=f"Os logs de **{categoria.upper()}** serão enviados em {canal.mention}.",
                color=discord.Color.brand_green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("❌ Erro ao salvar no banco de dados.", ephemeral=True)

    @set_log_channel.autocomplete('categoria')
    async def category_autocomplete(self, interaction: discord.Interaction, current: str):
        categories = ["MAGIC_SQUARE", "SECRET_PEAK", "CLAIMS"]
        return [app_commands.Choice(name=cat, value=cat) for cat in categories if current.lower() in cat.lower()]

async def setup(bot):
    await bot.add_cog(LogsCog(bot))
