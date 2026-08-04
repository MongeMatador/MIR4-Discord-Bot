import logging
from typing import Dict, List, Any
from datetime import datetime
from config import MAP_DATA, logger

class ClaimService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClaimService, cls).__new__(cls)
            cls._instance._claims: Dict[str, Dict[str, Any]] = {}
            cls._active_panels: List[Any] = []
        return cls._instance

    def register_panel(self, panel_view):
        if panel_view not in self._active_panels:
            self._active_panels.append(panel_view)

    def unregister_panel(self, panel_view):
        if panel_view in self._active_panels:
            self._active_panels.remove(panel_view)

    async def sync_all_panels(self):
        dead_panels = []
        for panel in self._active_panels:
            try:
                await panel.refresh_panel()
            except Exception as e:
                logger.error(f"Erro ao sincronizar painel: {e}")
                dead_panels.append(panel)
        for dead in dead_panels:
            self.unregister_panel(dead)

    def get_rooms_for_floor(self, zone: str, floor: str) -> List[str]:
        if zone == "Square":
            floor_data = MAP_DATA["MAGIC_SQUARE"]["floors"].get(floor, {})
            standard = floor_data.get("standard_rooms", [])
            antidemons_dict = floor_data.get("antidemons", {})
            
            adc_rooms = []
            for ad_name, ad_info in antidemons_dict.items():
                for room in ad_info["rooms"]:
                    adc_rooms.append(f"{ad_name} - {room}")
            return adc_rooms + standard
        else:
            return MAP_DATA["SECRET_PEAK"]["floors"].get(floor, {}).get("standard_rooms", [])

    async def make_claim(self, zone: str, floor: str, room: str, user_id: int, user_name: str, tickets: int = 1) -> Dict[str, Any]:
        claim_key = f"{zone}:{floor}:{room}"
        claim_data = {
            "claim_key": claim_key,
            "zone": zone,
            "floor": floor,
            "room": room,
            "user_id": user_id,
            "user_name": user_name,
            "tickets": tickets,
            "claimed_at": datetime.utcnow().isoformat()
        }
        self._claims[claim_key] = claim_data
        await self.sync_all_panels()
        return claim_data

    async def release_user_claims(self, user_id: int) -> int:
        keys_to_delete = [k for k, v in self._claims.items() if v["user_id"] == user_id]
        for k in keys_to_delete:
            del self._claims[k]
        
        if keys_to_delete:
            await self.sync_all_panels()
        return len(keys_to_delete)

    # Sintaxe de parâmetro corrigida
    def get_all_claims(self) -> Dict[str, Dict[str, Any]]:
        return self._claims

claim_service = ClaimService()
