import discord
from discord.ext import commands
from discord import app_commands

class ClaimCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setup_painel",
        description="Configura um painel de claims (canal de cliques) ou placar de andar (canal de placar)."
    )
    @app_commands.describe(
        map_type="Selecione o mapa para este painel",
        floor="Selecione o andar se for criar um placar de andar, ou deixe em branco para o painel de claims principal"
    )
    @app_commands.choices(
        map_type=[
            app_commands.Choice(name="🔮 Praça Mágica", value="MAGIC_SQUARE"),
            app_commands.Choice(name="🏔️ Pico Secreto", value="SECRET_PEAK")
        ],
        floor=[
            app_commands.Choice(name="6F", value="6F"),
            app_commands.Choice(name="7F", value="7F"),
            app_commands.Choice(name="8F", value="8F"),
            app_commands.Choice(name="9F", value="9F"),
            app_commands.Choice(name="10F", value="10F"),
            app_commands.Choice(name="11F", value="11F"),
            app_commands.Choice(name="12F", value="12F")
        ]
    )
    @commands.has_permissions(administrator=True)
    async def setup_painel(self, interaction: discord.Interaction, map_type: str, floor: str = None):
        await interaction.response.defer(ephemeral=True)
        floor_key = floor if floor else ""
        
        await self.bot.panel_service.update_panel(
            guild_id=interaction.guild_id,
            map_type=map_type,
            floor=floor_key,
            target_channel=interaction.channel
        )
        
        lbl = "Praça Mágica" if map_type == "MAGIC_SQUARE" else "Pico Secreto"
        if floor_key:
            msg = f"✅ Placar de monitoramento em tempo real de **{lbl} - {floor_key}** ativado e sincronizado!"
        else:
            msg = f"✅ Painel de claims principal de **{lbl}** ativado e sincronizado!"
            
        await interaction.followup.send(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClaimCog(bot))
