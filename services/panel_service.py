import asyncio
import discord
from database.repositories.panel_repository import PanelRepository
from database.repositories.claim_repository import ClaimRepository
from ui.embeds import MIR4Embeds
from config import logger

class PanelService:
    """Gerenciador atômico do painel de controle da guilda."""
    def __init__(self, bot, panel_repo: PanelRepository, claim_repo: ClaimRepository):
        self.bot = bot
        self.panel_repo = panel_repo
        self.claim_repo = claim_repo
        self._locks = {}

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    async def update_panel(self, guild_id: int, map_type: str = None, target_channel: discord.TextChannel = None):
        """Atualiza os painéis correspondentes."""
        async with self._get_lock(guild_id):
            if map_type:
                await self._update_single_panel(guild_id, map_type, target_channel)
            else:
                await self._update_single_panel(guild_id, "MAGIC_SQUARE", target_channel)
                await self._update_single_panel(guild_id, "SECRET_PEAK", target_channel)

    async def _update_single_panel(self, guild_id: int, map_type: str, target_channel: discord.TextChannel = None):
        from ui.views import MIR4MSPanelPersistentView, MIR4PSPanelPersistentView
        
        # Gera o Embed correto
        embed = MIR4Embeds.build_panel_embed(map_type)
        view = MIR4MSPanelPersistentView(self.bot) if map_type == "MAGIC_SQUARE" else MIR4PSPanelPersistentView(self.bot)
        
        panel_info = await self.panel_repo.get_panel(guild_id, map_type)
        if panel_info:
            channel_id, message_id = panel_info
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    await message.edit(embed=embed, view=view)
                    logger.info(f"[PANEL SERVICE] Painel {map_type} editado com sucesso na Guild {guild_id}.")
                    return
                except discord.NotFound:
                    logger.warning(f"[PANEL SERVICE] Mensagem antiga de {map_type} não encontrada. Recriando...")

        dest_channel = target_channel or (self.bot.get_channel(panel_info) if panel_info else None)
        if dest_channel:
            new_msg = await dest_channel.send(embed=embed, view=view)
            await self.panel_repo.save_panel(guild_id, map_type, dest_channel.id, new_msg.id)
            logger.info(f"[PANEL SERVICE] Novo painel de {map_type} criado e registrado para Guild {guild_id}.")
