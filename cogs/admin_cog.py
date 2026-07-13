import discord
from discord.ext import commands
from config import Config
from services.claim_service import DatabaseManager

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="link_floor")
    @commands.has_permissions(administrator=True)
    async def link_floor(self, ctx: commands.Context, map_type: str, floor: str, channel_arg: str):
        map_upper = map_type.upper()
        floor_upper = floor.upper()
        
        if map_upper not in Config.MAP_DATA:
            return await ctx.send("❌ Tipo de mapa inválido! Use `MAGIC_SQUARE` ou `SECRET_PEAK`.")
            
        if floor_upper not in Config.MAP_DATA[map_upper]["floors"]:
            return await ctx.send(f"❌ Esse andar não existe no mapeamento tático desse mapa.")
            
        # RESOLUÇÃO DEFENSIVA DE INPUT: Extrai a ID eliminando falhas de acentuação do Discord
        channel_id = None
        clean_arg = channel_arg.replace("<#", "").replace(">", "")
        if clean_arg.isdigit():
            channel_id = int(clean_arg)
        else:
            channel = discord.utils.get(ctx.guild.text_channels, name=channel_arg.replace("#", ""))
            if channel:
                channel_id = channel.id

        if not channel_id:
            return await ctx.send(f"❌ Canal `{channel_arg}` não pôde ser resolvido estruturalmente.")
            
        resolved_channel = ctx.guild.get_channel(channel_id)
        async with DatabaseManager.get_connection() as db:
            await db.execute(
                """INSERT INTO floor_dashboards (map_type, floor, channel_id, message_id)
                   VALUES (?, ?, ?, NULL)
                   ON CONFLICT(map_type, floor) DO UPDATE SET channel_id = excluded.channel_id, message_id = NULL""",
                (map_upper, floor_upper, resolved_channel.id)
            )
            await db.commit()
        await ctx.send(f"✅ Painel Sincronizado para **{Config.MAP_DATA[map_upper]['label']} ({floor_upper})** no canal {resolved_channel.mention}.")

    @commands.command(name="set_log_channel")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx: commands.Context, map_type: str, channel_arg: str):
        map_upper = map_type.upper()
        if map_upper not in ["MAGIC_SQUARE", "SECRET_PEAK"]:
            return await ctx.send("❌ Escolha estritamente entre `MAGIC_SQUARE` ou `SECRET_PEAK`.")
            
        channel_id = None
        clean_arg = channel_arg.replace("<#", "").replace(">", "")
        if clean_arg.isdigit():
            channel_id = int(clean_arg)
        else:
            channel = discord.utils.get(ctx.guild.text_channels, name=channel_arg.replace("#", ""))
            if channel:
                channel_id = channel.id

        if not channel_id:
            return await ctx.send(f"❌ Canal de destino `{channel_arg}` inválido ou não encontrado.")

        resolved_channel = ctx.guild.get_channel(channel_id)
        setting_key = f"log_channel_id_{map_upper}"
        
        async with DatabaseManager.get_connection() as db:
            await db.execute(
                "INSERT INTO admin_settings (setting_key, setting_value) VALUES (?, ?) ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value",
                (setting_key, str(resolved_channel.id))
            )
            await db.commit()
        await ctx.send(f"🔒 Canal de Log de Auditoria para **{map_upper}** fixado com sucesso em: {resolved_channel.mention}.")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))