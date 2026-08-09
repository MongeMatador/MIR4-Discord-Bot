import discord
from config import Config

class ClaimWizardView(discord.ui.View):
    def __init__(self, bot, map_type: str):
        super().__init__(timeout=120)
        self.bot = bot
        self.map_type = map_type
        self.floor = None
        self.spot = None
        self.room_number = 1
        self.tickets = 1

        # Começa adicionando diretamente o seletor de Andares com base no mapa correto! (Pula a etapa de escolher mapa!)
        self.add_item(FloorSelect(self.map_type))

class FloorSelect(discord.ui.Select):
    def __init__(self, map_type):
        floors = list(Config.MAP_DATA[map_type]["floors"].keys())
        options = [discord.SelectOption(label=f"Floor {f}", value=f) for f in floors]
        super().__init__(placeholder="Select Floor / Selecione o Andar", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.floor = self.values[0] # FIX: Pegando a string de dentro da lista
        
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
        view.spot = self.values[0] # FIX: Pegando a string de dentro da lista
        
        spots_info = Config.MAP_DATA[view.map_type]["floors"][view.floor][view.spot]
        max_rooms = spots_info.get("rooms", 1)
        
        view.clear_items()
        lbl = Config.MAP_DATA[view.map_type]['label']
        
        if max_rooms > 1:
            view.add_item(RoomSelect(max_rooms))
            msg = f"🗺️ Map: **{lbl}** | Floor: **{view.floor}** | Spot: **{view.spot}**\n➡️ Select the Room (Chamber Instance):"
            await interaction.response.edit_message(content=msg, view=view)
        else:
            view.room_number = 1
            view.add_item(TicketSelect(view.map_type, view.floor, view.spot))
            msg = f"🗺️ Map: **{lbl}** | Floor: **{view.floor}** | Spot: **{view.spot}** | Room: **1**\n➡️ How many Tickets?"
            await interaction.response.edit_message(content=msg, view=view)

class RoomSelect(discord.ui.Select):
    def __init__(self, max_rooms):
        options = [discord.SelectOption(label=f"Room {i}", value=str(i)) for i in range(1, max_rooms + 1)]
        super().__init__(placeholder="Select Room / Selecione a Sub-sala", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.room_number = int(self.values[0]) # FIX: Pegando a string de dentro da lista
        
        view.clear_items()
        view.add_item(TicketSelect(view.map_type, view.floor, view.spot))
        
        lbl = Config.MAP_DATA[view.map_type]['label']
        msg = f"🗺️ Map: **{lbl}** | Floor: **{view.floor}** | Spot: **{view.spot}** | Room: **{view.room_number}**\n➡️ How many Tickets?"
        await interaction.response.edit_message(content=msg, view=view)

class TicketSelect(discord.ui.Select):
    def __init__(self, map_type, floor, spot):
        spots_info = Config.MAP_DATA[map_type]["floors"][floor][spot]
        allowed_tickets = spots_info.get("tickets", list((1, 2, 3)))
        options = [discord.SelectOption(label=f"{t} Ticket(s)", value=str(t)) for t in allowed_tickets]
        super().__init__(placeholder="Select Tickets / Quantidade de Tickets", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.tickets = int(self.values[0]) # FIX: Pegando a string de dentro da lista
        
        view.clear_items()
        await interaction.response.defer(ephemeral=True)
        
        map_label = "Magic Square" if view.map_type == "MAGIC_SQUARE" else "Secret Peak"
        spot_string = f"{map_label} {view.floor} - {view.spot} - Room {view.room_number} ({view.tickets} Tk)"
        
        success = await view.bot.claim_service.register_claim(
            interaction.guild_id, interaction.user, spot_string
        )
        
        if success:
            msg = f"✅ **Claim Successful!**\nYou successfully claimed: **{spot_string}**"
            await interaction.followup.send(msg, ephemeral=True)
        else:
            msg = f"❌ **Claim Failed!**\nThe spot **{spot_string}** is already occupied or you already have an active claim!"
            await interaction.followup.send(msg, ephemeral=True)

class MIR4MSPanelPersistentView(discord.ui.View):
    """Painel de claims exclusivo para a Praça Mágica."""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Claim Spot (Praça)", style=discord.ButtonStyle.green, custom_id="mir4:btn_claim:MAGIC_SQUARE")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "🧙‍♂️ **MIR4 Claim Wizard (Magic Square) starting...**\nSelect your floor below:"
        await interaction.response.send_message(content=msg, view=ClaimWizardView(self.bot, "MAGIC_SQUARE"), ephemeral=True)

    @discord.ui.button(label="Cancel Claim", style=discord.ButtonStyle.red, custom_id="mir4:btn_unclaim:MAGIC_SQUARE")
    async def unclaim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id
        claims = await self.bot.claim_repo.get_all_claims(guild_id)
        user_claims = [c for c in claims if c["user_id"] == interaction.user.id and ("Magic Square" in c["spot_name"] or "🔮" in c["spot_name"])]
        
        if not user_claims:
            msg = "⚠️ You do not have any active spots claimed on Magic Square."
            return await interaction.followup.send(msg, ephemeral=True)

        for c in user_claims:
            await self.bot.claim_service.release_claim(guild_id, interaction.user, c["spot_name"])

        msg = "✅ Your active claims on Magic Square have been released successfully!"
        await interaction.followup.send(msg, ephemeral=True)

class MIR4PSPanelPersistentView(discord.ui.View):
    """Painel de claims exclusivo para o Pico Secreto."""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Claim Spot (Pico)", style=discord.ButtonStyle.green, custom_id="mir4:btn_claim:SECRET_PEAK")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "🧙‍♂️ **MIR4 Claim Wizard (Secret Peak) starting...**\nSelect your floor below:"
        await interaction.response.send_message(content=msg, view=ClaimWizardView(self.bot, "SECRET_PEAK"), ephemeral=True)

    @discord.ui.button(label="Cancel Claim", style=discord.ButtonStyle.red, custom_id="mir4:btn_unclaim:SECRET_PEAK")
    async def unclaim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id
        claims = await self.bot.claim_repo.get_all_claims(guild_id)
        user_claims = [c for c in claims if c["user_id"] == interaction.user.id and ("Secret Peak" in c["spot_name"] or "🏔️" in c["spot_name"])]
        
        if not user_claims:
            msg = "⚠️ You do not have any active spots claimed on Secret Peak."
            return await interaction.followup.send(msg, ephemeral=True)

        for c in user_claims:
            await self.bot.claim_service.release_claim(guild_id, interaction.user, c["spot_name"])

        msg = "✅ Your active claims on Secret Peak have been released successfully!"
        await interaction.followup.send(msg, ephemeral=True)
