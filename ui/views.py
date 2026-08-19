import discord
from config import Config

class ClaimWizardView(discord.ui.View):
    def __init__(self, bot, map_type: str):
        super().__init__(timeout=120)
        self.bot = bot
        self.map_type = map_type
        self.floor = None
        self.spot = None
        self.tickets = 1
        self.add_item(FloorSelect(self.map_type))

class FloorSelect(discord.ui.Select):
    def __init__(self, map_type):
        floors = list(Config.MAP_DATA[map_type]["floors"].keys())
        options = [discord.SelectOption(label=f"Floor {f}", value=f) for f in floors]
        super().__init__(placeholder="Select Floor / Selecione o Andar", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.floor = self.values[0] # EXTRAÇÃO CORRETA ✅
        view.clear_items()
        view.add_item(SpotSelect(view.map_type, view.floor))
        lbl = Config.MAP_DATA[view.map_type]['label']
        msg = f"🗺️ Map: **{lbl}** | Floor: **{view.floor}**\n➡️ Now select the Spot:"
        await interaction.response.edit_message(content=msg, view=view)

class SpotSelect(discord.ui.Select):
    def __init__(self, map_type, floor):
        spots = Config.MAP_DATA[map_type]["floors"][floor]
        options = []
        for s, info in spots.items():
            options.append(discord.SelectOption(
                label=s,
                emoji=info.get("emoji", "📍"),
                value=s
            ))
        super().__init__(placeholder="Select Spot / Selecione o Spot", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.spot = self.values[0] # EXTRAÇÃO CORRETA ✅
        view.clear_items()
        
        # PULA QUARTO: Direto para a seleção de Tickets! O banco aloca de forma automática
        view.add_item(TicketSelect(view.map_type, view.floor, view.spot))
        lbl = Config.MAP_DATA[view.map_type]['label']
        msg = f"🗺️ Map: **{lbl}** | Floor: **{view.floor}** | Spot: **{view.spot}**\n➡️ How many Tickets?"
        await interaction.response.edit_message(content=msg, view=view)

class TicketSelect(discord.ui.Select):
    def __init__(self, map_type, floor, spot):
        spots_info = Config.MAP_DATA[map_type]["floors"][floor][spot]
        allowed_tickets = spots_info.get("tickets") or [1, 3, 6] # CORRIGIDO ✅
        ticket_labels = {
            1: "1 Ticket (30m)",
            2: "2 Tickets (1h)",
            3: "3 Tickets (1h30)",
            6: "6 Tickets (3h)"
        }
        options = []
        for t in allowed_tickets:
            label = ticket_labels.get(t, f"{t} Ticket(s)")
            options.append(discord.SelectOption(label=label, value=str(t)))
        super().__init__(placeholder="Select Tickets / Quantidade de Tickets", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.tickets = int(self.values[0]) # EXTRAÇÃO E CONVERSÃO CORRETA ✅
        view.clear_items()
        
        # ⚡ FEEDBACK INSTANTÂNEO: Altera a mensagem na hora, eliminando travamento visual!
        await interaction.response.edit_message(content="⌛ **Processando seu claim no Supabase... Por favor, aguarde.**", view=None)
        
        success, outcome_msg = await view.bot.claim_service.register_claim(
            interaction.guild_id, interaction.user, view.map_type, view.floor, view.spot, view.tickets
        )
        await interaction.followup.send(outcome_msg, ephemeral=True)

class MIR4MSPanelPersistentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Claim Spot (Praça)", style=discord.ButtonStyle.green, custom_id="mir4:btn_claim:MAGIC_SQUARE")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "🧙‍♂️ **MIR4 Claim Wizard (Magic Square) starting...**\nSelect your floor below:"
        await interaction.response.send_message(content=msg, view=ClaimWizardView(self.bot, "MAGIC_SQUARE"), ephemeral=True)

    @discord.ui.button(label="Cancel Claim / Fila", style=discord.ButtonStyle.red, custom_id="mir4:btn_unclaim:MAGIC_SQUARE")
    async def unclaim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        outcome_msg = await self.bot.claim_service.release_claim(interaction.guild_id, interaction.user, "MAGIC_SQUARE")
        await interaction.followup.send(outcome_msg, ephemeral=True)

class MIR4PSPanelPersistentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Claim Spot (Pico)", style=discord.ButtonStyle.green, custom_id="mir4:btn_claim:SECRET_PEAK")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "🧙‍♂️ **MIR4 Claim Wizard (Secret Peak) starting...**\nSelect your floor below:"
        await interaction.response.send_message(content=msg, view=ClaimWizardView(self.bot, "SECRET_PEAK"), ephemeral=True)

    @discord.ui.button(label="Cancel Claim / Fila", style=discord.ButtonStyle.red, custom_id="mir4:btn_unclaim:SECRET_PEAK")
    async def unclaim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        outcome_msg = await self.bot.claim_service.release_claim(interaction.guild_id, interaction.user, "SECRET_PEAK")
        await interaction.followup.send(outcome_msg, ephemeral=True)

class FloorEventButtonsView(discord.ui.View):
    def __init__(self, bot, map_type: str, floor: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.map_type = map_type
        self.floor = floor
        valid_events = Config.get_valid_events_for_floor(self.map_type, self.floor)
        for evt in valid_events:
            evt_config = Config.TRACKABLE_EVENTS[self.map_type][evt]
            self.add_item(FloorEventButton(self.bot, self.map_type, self.floor, evt, evt_config))

class FloorEventButton(discord.ui.Button):
    def __init__(self, bot, map_type: str, floor: str, event_key: str, config: dict):
        self.bot = bot
        self.map_type = map_type
        self.floor = floor
        self.event_key = event_key
        super().__init__(
            label=config["label"],
            emoji=config["emoji"],
            style=discord.ButtonStyle.secondary,
            custom_id=f"mir4:evt:{map_type}:{floor}:{event_key}"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        success, outcome_msg = await self.bot.claim_service.trigger_floor_event(
            interaction.guild_id, interaction.user, self.map_type, self.floor, self.event_key
        )
        await interaction.followup.send(outcome_msg, ephemeral=True)
