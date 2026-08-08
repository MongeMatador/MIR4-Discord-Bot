import discord
from database.repositories.log_repository import LogRepository
from utils.logger import log
from datetime import datetime

class LogService:
    """Serviço responsável por formatar e despachar os logs de Claims para o Discord."""

    def __init__(self, bot, log_repo: LogRepository):
        self.bot = bot
        self.log_repo = log_repo

    async def dispatch_claim_log(self, guild_id: int, user: discord.User, spot_name: str, action: str):
        """
        Despacha o log de ação de Claim (CLAIM / UNCLAIM / FORCE_UNCLAIM).
        Category padrão: MAGIC_SQUARE / SECRET_PEAK ou CLAIMS_LOG
        """
        # Tenta buscar canal específico da categoria ou o genérico 'CLAIMS'
        channel_id = await self.log_repo.get_log_channel_id(guild_id, "MAGIC_SQUARE") \
                     or await self.log_repo.get_log_channel_id(guild_id, "CLAIMS")

        if not channel_id:
            log.warning(f"[LOG SERVICE] Nenhum canal de log configurado para a Guild {guild_id}. O log foi ignorado.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                log.error(f"[LOG SERVICE] Erro ao buscar canal de log ID {channel_id}: {e}")
                return

        # Montagem do Embed
        if action == "CLAIM":
            color = discord.Color.brand_green()
            title = "⚔️ Novo Claim Registrado!"
            description = f"O jogador {user.mention} (`{user.display_name}`) reivindicou um spot."
        elif action == "UNCLAIM":
            color = discord.Color.orange()
            title = "🔓 Spot Liberado"
            description = f"O jogador {user.mention} (`{user.display_name}`) liberou o spot."
        else:
            color = discord.Color.red()
            title = "🧹 Claim Removido por Admin"
            description = f"O spot de {user.mention} foi limpo por ação administrativa."

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📍 Spot / Praça / Pico", value=f"`{spot_name}`", inline=True)
        embed.add_field(name="👤 Usuário", value=f"{user.mention} (ID: `{user.id}`)", inline=True)
        embed.set_footer(text="MIR4 Log System • Render Active")

        try:
            await channel.send(embed=embed)
            log.info(f"[LOG SERVICE] Log de {action} enviado com sucesso no canal {channel_id}.")
        except discord.Forbidden:
            log.error(f"[LOG SERVICE] Permissão negada ao enviar log no canal {channel_id}.")
        except Exception as e:
            log.error(f"[LOG SERVICE] Falha ao enviar log: {e}", exc_info=True)
