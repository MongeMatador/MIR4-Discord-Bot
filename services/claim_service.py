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
        # Coexistência multi-contas: Só valida se o jogador já possui claim ativo NO MESMO MAPA!
        map_type = "MAGIC_SQUARE" if "Magic Square" in spot_name or "🔮" in spot_name else "SECRET_PEAK"
        claims = await self.claim_repo.get_all_claims(guild_id)
        
        user_map_claims = [c for c in claims if c["user_id"] == user.id and (
            ("Magic Square" in c["spot_name"] or "🔮" in c["spot_name"]) if map_type == "MAGIC_SQUARE" else 
            ("Secret Peak" in c["spot_name"] or "🏔️" in c["spot_name"])
        )]
        
        if user_map_claims:
            return False

        success = await self.claim_repo.claim_spot(guild_id, spot_name, user.id, user.display_name)
        if success:
            await self.panel_service.update_panel(guild_id, map_type)
            await self.log_service.dispatch_claim_log(guild_id, user, spot_name, "CLAIM")
            return True
        return False

    async def release_claim(self, guild_id: int, user: discord.User, spot_name: str) -> bool:
        success = await self.claim_repo.unclaim_spot(guild_id, spot_name, user.id)
        if success:
            map_type = "MAGIC_SQUARE" if "Magic Square" in spot_name or "🔮" in spot_name else "SECRET_PEAK"
            await self.panel_service.update_panel(guild_id, map_type)
            await self.log_service.dispatch_claim_log(guild_id, user, spot_name, "UNCLAIM")
            return True
        return False
