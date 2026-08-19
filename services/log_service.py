import discord
from database.connection import DatabaseManager
from config import logger
from datetime import datetime

class LogService:
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild_id: int, category: str) -> int:
        async with DatabaseManager.get_connection() as db:
            async with db.execute(
                "SELECT channel_id FROM guild_log_channels WHERE guild_id = ? AND category = ?",
                (guild_id, category.upper())
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def dispatch_claim_log(self, guild_id: int, user: discord.User, map_type: str, floor: str, spot_type: str, room_number: int, action: str, details: str = ""):
        chan_id = await self.get_log_channel(guild_id, map_type)
        if not chan_id:
            return
        channel = self.bot.get_channel(chan_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(chan_id)
            except:
                return

        color = discord.Color.green() if "CLAIM" in action else discord.Color.orange()
        title = f"⚔️ Novo Claim - {map_type.replace('_', ' ')}" if "CLAIM" in action else f"🔓 Claim Liberado - {map_type.replace('_', ' ')}"
        
        embed = discord.Embed(title=title, color=color, timestamp=datetime.utcnow())
        embed.add_field(name="👤 Usuário", value=f"{user.mention} ({user.display_name})", inline=True)
        embed.add_field(name="📍 Local", value=f"{floor} - {spot_type} (Sala {room_number})", inline=True)
        if details:
            embed.add_field(name="⏱️ Detalhes", value=details, inline=False)
        embed.set_footer(text="MIR4 Audit Log System")
        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro ao enviar log: {e}")
