import discord
from discord.ui import View, Button
from config import Config
from services.claim_service import ClaimService

class FloorEventButtonsView(View):
    def __init__(self, map_type: str, floor: str):
        super().__init__(timeout=None)
        self.map_type = map_type
        self.floor = floor
        self._generate_buttons()

    def _generate_buttons(self):
        valid_keys = Config.get_valid_events_for_floor(self.map_type, self.floor)
        events = Config.TRACKABLE_EVENTS[self.map_type]
        
        for event_key in valid_keys:
            data = events[event_key]
            btn = Button(
                label=data["label"],
                style=discord.ButtonStyle.secondary,
                emoji=data["emoji"],
                custom_id=f"evt:{self.map_type}:{self.floor}:{event_key}"
            )
            btn.callback = self.button_callback
            self.add_item(btn)

    async def button_callback(self, interaction: discord.Interaction):
        _, map_type, floor, event_key = interaction.data["custom_id"].split(":")
        
        # BARREIRA DE PRIVILÉGIO: Dono do Boss gerencia os tempos de respawn do andar
        boss_owner_id = await ClaimService.get_boss_owner(map_type, floor)
        
        if boss_owner_id is None:
            return await interaction.response.send_message(
                "❌ **Acesso Negado!** Esta rotação está bloqueada porque o **BOSS** deste andar se encontra livre. Reivindique o Boss para ganhar autorização.",
                ephemeral=True
            )
            
        if boss_owner_id != interaction.user.id:
            return await interaction.response.send_message(
                f"❌ **Acesso Negado!** Somente o líder tático em posse do **BOSS** deste andar (<@{boss_owner_id}>) possui autorização.",
                ephemeral=True
            )
            
        import_datetime = __import__('datetime').datetime
        now_utc = import_datetime.utcnow()
        await ClaimService.update_event_time(map_type, floor, event_key, now_utc.isoformat())
        
        server_time = now_utc + __import__('datetime').timedelta(hours=Config.TIMEZONE_OFFSET)
        event_label = Config.TRACKABLE_EVENTS[map_type][event_key]["label"]
        
        await interaction.response.send_message(
            f"✅ **{event_label}** registrado às **{server_time.strftime('%H:%M')}** no **{floor}**!",
            ephemeral=True
        )
        
        claim_cog = interaction.client.get_cog("ClaimCog")
        if claim_cog:
            await claim_cog.update_floor_dashboard(map_type, floor)