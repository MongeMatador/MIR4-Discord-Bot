import asyncio
import discord
from database.repositories.panel_repository import PanelRepository
from database.repositories.claim_repository import ClaimRepository
from ui.embeds import MIR4Embeds
from database.connection import DatabaseConnection
from config import logger

class PanelService:
    """Gerenciador atômico dos painéis e placares de andares da guilda."""
    def __init__(self, bot, panel_repo: PanelRepository, claim_repo: ClaimRepository):
        self.bot = bot
        self.panel_repo = panel_repo
        self.claim_repo = claim_repo
        self._locks = {}

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    async def update_panel(self, guild_id: int, map_type: str = None, floor: str = None, target_channel: discord.TextChannel = None):
        """Atualiza um painel específico ou redesenha todos os placares registrados na guilda."""
        async with self._get_lock(guild_id):
            if map_type:
                await self._update_single_panel(guild_id, map_type, floor, target_channel)
            else:
                # Se nada for passado, atualiza tudo de uma vez buscando no banco
                try:
                    async with DatabaseConnection.get_connection() as db:
                        async with db.execute(
                            "SELECT map_type, floor FROM panel_settings WHERE guild_id = ?", (guild_id,)
                        ) as cursor:
                            rows = await cursor.fetchall()
                            for r in rows:
                                await self._update_single_panel(guild_id, r[0], r[1])
                except Exception as e:
                    logger.error(f"[PANEL SERVICE UPDATE ALL ERROR]: {e}")

    async def _update_single_panel(self, guild_id: int, map_type: str, floor: str = None, target_channel: discord.TextChannel = None):
        from ui.views import MIR4MSPanelPersistentView, MIR4PSPanelPersistentView
        
        floor_key = floor if floor else ""
        claims = await self.claim_repo.get_all_claims(guild_id)

        # Se houver andar, exibe o placar de andares. Se não, o painel estático trilingue.
        if floor_key:
            embed = MIR4Embeds.build_floor_embed(map_type, floor_key, claims)
            view = None # Placares de andares são apenas visualização
        else:
            embed = MIR4Embeds.build_panel_embed(map_type)
            view = MIR4MSPanelPersistentView(self.bot) if map_type == "MAGIC_SQUARE" else MIR4PSPanelPersistentView(self.bot)

        panel_info = await self.panel_repo.get_panel(guild_id, map_type, floor_key)
        if panel_info:
            channel_id, message_id = panel_info
            channel = self.bot.get_channel(channel_id)
            if not channel:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except Exception:
                    channel = None
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    await message.edit(embed=embed, view=view)
                    logger.info(f"[PANEL SERVICE] Editado: {map_type} {floor_key} na Guild {guild_id}.")
                    return
                except discord.NotFound:
                    logger.warning("[PANEL SERVICE] Mensagem antiga não encontrada. Recriando...")

        dest_channel = target_channel or (self.bot.get_channel(panel_info[0]) if panel_info else None)
        if dest_channel:
            new_msg = await dest_channel.send(embed=embed, view=view)
            await self.panel_repo.save_panel(guild_id, map_type, floor_key, dest_channel.id, new_msg.id)
            logger.info(f"[PANEL SERVICE] Criado novo painel: {map_type} {floor_key} na Guild {guild_id}.")
