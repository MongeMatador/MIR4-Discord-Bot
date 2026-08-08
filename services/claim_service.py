import discord
from database.repositories.claim_repository import ClaimRepository
from services.panel_service import PanelService
from services.log_service import LogService

class ClaimService:
    """Serviço de orquestração de ocupações."""

    def __init__(self, claim_repo: ClaimRepository, panel_service: PanelService, log_service: LogService):
        self.claim_repo = claim_repo
        self.panel_service = panel_service
        self.log_service = log_service

    async def register_claim(self, guild_id: int, user: discord.User, spot_name: str) -> bool:
        success = await self.claim_repo.claim_spot(guild_id, spot_name, user.id, user.display_name)
        if success:
            await self.panel_service.update_panel(guild_id)
            await self.log_service.dispatch_claim_log(guild_id, user, spot_name, "CLAIM")
            return True
        return False

    async def release_claim(self, guild_id: int, user: discord.User, spot_name: str) -> bool:
        success = await self.claim_repo.unclaim_spot(guild_id, spot_name, user.id)
        if success:
            await self.panel_service.update_panel(guild_id)
            await self.log_service.dispatch_claim_log(guild_id, user, spot_name, "UNCLAIM")
            return True
        return False
