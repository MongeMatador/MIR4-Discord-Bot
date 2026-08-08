import discord
from config import Config

class ClaimWizardView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot
        self.map_type = None
        self.floor = None
        self.spot = None
        self.room_number = 1
        self.tickets = 1

        # Começa adicionando o seletor de Mapas
        self.add_item(MapSelect())

class MapSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Magic Square", 
                emoji="🔮", 
                value="MAGIC_SQUARE"
            ),
            discord.SelectOption(
                label="Secret Peak", 
                emoji="🏔️", 
                value="SECRET_PEAK"
            )
        ]
        super().__init__(
            placeholder="Select Map / Selecione o Mapa", 
            options=options, 
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.map_type = self.values[0]
        
        # Remove o seletor atual e adiciona o de andares
        view.clear_items()
        view.add_item(FloorSelect(view.map_type))
        
        lbl = Config.MAP_DATA[view.map_type]['label']
        msg = (
            f"🗺️ Map selected: **{lbl}**\n"
            "➡️ Now select the Floor:"
        )
        await interaction.response.edit_message(content=msg, view=view)

class FloorSelect(discord.ui.Select):
    def __init__(self, map_type):
        floors = list(Config.MAP_DATA[map_type]["floors"].keys())
        options = [
            discord.SelectOption(label=f"Floor {f}", value=f) 
            for f in floors
        ]
        super().__init__(
            placeholder="Select Floor / Selecione o Andar", 
            options=options, 
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.floor = self.values[0]
        
        view.clear_items()
        view.add_item(SpotSelect(view.map_type, view.floor))
        
        lbl = Config.MAP_DATA[view.map_type]['label']
        msg = (
            f"🗺️ Map: **{lbl}** | Floor: **{view.floor}**\n"
            "➡️ Now select the Spot:"
        )
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
        super().__init__(
            placeholder="Select Spot / Selecione o Spot", 
            options=options, 
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.spot = self.values[0]
        
        spots_info = Config.MAP_DATA[view.map_type]["floors"][view.floor][view.spot]
        max_rooms = spots_info.get("rooms", 1)
        
        view.clear_items()
        lbl = Config.MAP_DATA[view.map_type]['label']
        
        # Se a sala possuir múltiplas instâncias (ex: ADC1, ADC2, ADC3 possuem 3 sub-salas)
        if max_rooms > 1:
            view.add_item(RoomSelect(max_rooms))
            msg = (
                f"🗺️ Map: **{lbl}** | Floor: **{view.floor}** | "
                f"Spot: **{view.spot}**\n"
                "➡️ Select the Room (Chamber Instance):"
            )
            await interaction.response.edit_message(content=msg, view=view)
        else:
            view.room_number = 1
            view.add_item(TicketSelect(view.map_type, view.floor, view.spot))
            msg = (
                f"🗺️ Map: **{lbl}** | Floor: **{view.floor}** | "
                f"Spot: **{view.spot}** | Room: **1**\n"
                "➡️ How many Tickets?"
            )
            await interaction.response.edit_message(content=msg, view=view)

class RoomSelect(discord.ui.Select):
    def __init__(self, max_rooms):
        options = [
            discord.SelectOption(label=f"Room {i}", value=str(i)) 
            for i in range(1, max_rooms + 1)
        ]
        super().__init__(
            placeholder="Select Room / Selecione a Sub-sala", 
            options=options, 
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.room_number = int(self.values[0])
        
        view.clear_items()
        view.add_item(TicketSelect(view.map_type, view.floor, view.spot))
        
        lbl = Config.MAP_DATA[view.map_type]['label']
        msg = (
            f"🗺️ Map: **{lbl}** | Floor: **{view.floor}** | "
            f"Spot: **{view.spot}** | Room: **{view.room_number}**\n"
            "➡️ How many Tickets?"
        )
        await interaction.response.edit_message(content=msg, view=view)

class TicketSelect(discord.ui.Select):
    def __init__(self, map_type, floor, spot):
        spots_info = Config.MAP_DATA[map_type]["floors"][floor][spot]
        allowed_tickets = spots_info.get("tickets", list((1, 2, 3)))
        options = [
            discord.SelectOption(label=f"{t} Ticket(s)", value=str(t)) 
            for t in allowed_tickets
        ]
        super().__init__(
            placeholder="Select Tickets / Quantidade de Tickets", 
            options=options, 
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.tickets = int(self.values[0])
        
        view.clear_items()
        await interaction.response.defer(ephemeral=True)
        
        # Formata o spot em inglês para salvar no Banco de Dados
        map_label = "Magic Square" if view.map_type == "MAGIC_SQUARE" else "Secret Peak"
        spot_string = (
            f"{map_label} {view.floor} - {view.spot} - "
            f"Room {view.room_number} ({view.tickets} Tk)"
        )
        
        # Registra a reivindicação compatível com a sua arquitetura atual
        success = await view.bot.claim_service.register_claim(
            interaction.guild_id, interaction.user, spot_string
        )
        
        if success:
            msg = (
                "✅ **Claim Successful!**\n"
                f"You successfully claimed: **{spot_string}**"
            )
            await interaction.followup.send(msg, ephemeral=True)
        else:
            msg = (
                "❌ **Claim Failed!**\n"
                f"The spot **{spot_string}** is already occupied "
                "or you already have an active claim in this map!"
            )
            await interaction.followup.send(msg, ephemeral=True)

class MIR4PanelPersistentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Claim Spot", 
        style=discord.ButtonStyle.green, 
        custom_id="mir4:btn_claim"
    )
    async def claim_button(
        self, 
        interaction: discord.Interaction, 
        button: discord.ui.Button
    ):
        msg = (
            "🧙‍♂️ **MIR4 Claim Wizard starting...**\n"
            "Select your destination below:"
        )
        await interaction.response.send_message(
            content=msg,
            view=ClaimWizardView(self.bot),
            ephemeral=True
        )

    @discord.ui.button(
        label="Cancel Claim / Fila", 
        style=discord.ButtonStyle.red, 
        custom_id="mir4:btn_unclaim"
    )
    async def unclaim_button(
        self, 
        interaction: discord.Interaction, 
        button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id

        claims = await self.bot.claim_repo.get_all_claims(guild_id)
        user_claims = [c for c in claims if c["user_id"] == interaction.user.id]

        if not user_claims:
            msg = "⚠️ You do not have any active spots claimed."
            return await interaction.followup.send(msg, ephemeral=True)

        for c in user_claims:
            await self.bot.claim_service.release_claim(
                guild_id, 
                interaction.user, 
                c["spot_name"]
            )

        msg = "✅ Your active claims have been released successfully!"
        await interaction.followup.send(msg, ephemeral=True)
