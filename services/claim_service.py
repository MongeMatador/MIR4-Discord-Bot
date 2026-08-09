import discord
from database.repositories.claim_repository import ClaimRepository
from services.panel_service import PanelService
from services.log_service import LogService

class ClaimService:
    """Serviço de orquestração de ocupações de spots."""
    def __init__(self, claim_repo: ClaimRepository, panel_service: PanelService, log_service: LogService):
        self.claim_repo = claim_repo
        self.panel_service = panel_service
        self.log_service = log_service

    async def register_claim(self, guild_id: int, user: discord.User, spot_name: str) -> bool:
        success = await self.claim_repo.claim_spot(guild_id, spot_name, user.id, user.display_name)
        if success:
            map_type = "MAGIC_SQUARE" if "Magic Square" in spot_name or "🔮" in spot_name else "SECRET_PEAK"
            
            # Extrai o andar (ex: "12F") para saber se precisa atualizar algum placar de andar
            floor = None
            for f in ["6F", "7F", "8F", "9F", "10F", "11F", "12F"]:
                if f in spot_name:
                    floor = f
                    break
            
            # Atualiza o painel principal
            await self.panel_service.update_panel(guild_id, map_type, "")
            # Atualiza o placar do andar correspondente
            if floor:
                await self.panel_service.update_panel(guild_id, map_type, floor)
                
            await self.log_service.dispatch_claim_log(guild_id, user, spot_name, "CLAIM")
            return True
        return False

    async def release_claim(self, guild_id: int, user: discord.User, spot_name: str) -> bool:
        success = await self.claim_repo.unclaim_spot(guild_id, spot_name, user.id)
        if success:
            map_type = "MAGIC_SQUARE" if "Magic Square" in spot_name or "🔮" in spot_name else "SECRET_PEAK"
            
            floor = None
            for f in ["6F", "7F", "8F", "9F", "10F", "11F", "12F"]:
                if f in spot_name:
                    floor = f
                    break
            
            await self.panel_service.update_panel(guild_id, map_type, "")
            if floor:
                await self.panel_service.update_panel(guild_id, map_type, floor)
                
            await self.log_service.dispatch_claim_log(guild_id, user, spot_name, "UNCLAIM")
            return True
        return False
