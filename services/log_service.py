import discord
from database.repositories.log_repository import LogRepository
from config import logger
from datetime import datetime

class LogService:
    """Serviço para despachar embeds de auditoria para o canal de logs."""

    def __init__(self, bot, log_repo: LogRepository):
        self.bot = bot
        self.log_repo = log_repo

    async def dispatch_claim_log(self, guild_id: int, user: discord.User, spot_name: str, action: str):
        channel_id = await self.log_repo.get_log_channel_id(guild_id, "MAGIC_SQUARE") \
                     or await self.log_repo.get_log_channel_id(guild_id, "CLAIMS")

        if not channel_id:
            logger.warning(f"[LOG SERVICE] Nenhum canal de log configurado na Guild {guild_id}.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                logger.error(f"[LOG SERVICE] Canal ID {channel_id} inacessível: {e}")
                return

        if action == "CLAIM":
            color = discord.Color.brand_green()
            title = "⚔️ Novo Claim Registrado!"
            description = f"O jogador {user.mention} (`{user.display_name}`) reivindicou um spot."
        else:
            color = discord.Color.orange()
            title = "🔓 Spot Liberado"
            description = f"O jogador {user.mention} (`{user.display_name}`) liberou o spot."

        embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
        embed.add_field(name="📍 Spot / Praça / Pico", value=f"`{spot_name}`", inline=True)
        embed.add_field(name="👤 Usuário", value=f"{user.mention} (ID: `{user.id}`)", inline=True)
        embed.set_footer(text="MIR4 Log System • Render Active")

        try:
            await channel.send(embed=embed)
            logger.info(f"[LOG SERVICE] Log de {action} enviado para o canal {channel_id}.")
        except Exception as e:
            logger.error(f"[LOG SERVICE] Erro de envio no Discord: {e}")
