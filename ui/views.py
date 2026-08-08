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
            discord.SelectOption(label="Magic Square", emoji="🔮", value="MAGIC_SQUARE"),
            discord.SelectOption(label="Secret Peak", emoji="🏔️", value="SECRET_PEAK")
        ]
        super().__init__(placeholder="Select the Map / Selecione o Mapa", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.map_type = self.values[0]
        
        # Remove o seletor atual e adiciona o de andares
        view.clear_items()
        view.add_item(FloorSelect(view.map_type))
        
        await interaction.response.edit_message(
            content=f"🗺️ Map selected: **{Config.MAP_DATA[view.map_type]['label']}**\n➡️ Now select the Floor:",
            view=view
        )

class FloorSelect(discord.ui.Select):
    def __init__(self, map_type):
        floors = list(Config.MAP_DATA[map_type]["floors"].keys())
        options = [discord.SelectOption(label=f"Floor {f}", value=f) for f in floors]
        super().__init__(placeholder="Select the Floor / Selecione o Andar", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.floor = self.values[0]
        
        view.clear_items()
        view.add_item(SpotSelect(view.map_type, view.floor))
        
        map_label = Config.MAP_DATA[view.map_type]['label']
        await interaction.response.edit_message(
            content=f"🗺️ Map: **{map_label}** | Floor: **{view.floor}**\n➡️ Now select the Spot:",
            view=view
        )

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
        super().__init__(placeholder="Select the Spot / Selecione o Spot", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.spot = self.values[0]
        
        spots_info = Config.MAP_DATA[view.map_type]["floors"][view.floor][view.spot]
        max_rooms = spots_info.get("rooms", 1)
        
        view.clear_items()
        
        # Se a sala possuir múltiplas instâncias (ex: ADC1, ADC2, ADC3 possuem 3 salas cada)
        if max_rooms > 1:
            view.add_item(RoomSelect(max_rooms))
            map_label = Config.MAP_DATA[view.map_type]['label']
            await interaction.response.edit_message(
                content=f"🗺️ Map: **{map_label}** | Floor: **{view.floor}** | Spot: **{view.spot}**\n➡️ Select the Room (Chamber Instance):",
                view=view
            )
        else:
            view.room_number = 1
            view.add_item(TicketSelect(view.map_type, view.floor, view.spot))
            map_label = Config.MAP_DATA[view.map_type]['label']
            await interaction.response.edit_message(
                content=f"🗺️ Map: **{map_label}** | Floor: **{view.floor}** | Spot: **{view.spot}** | Room: **1**\n➡️ How many Tickets?",
                view=view
            )

class RoomSelect(discord.ui.Select):
    def __init__(self, max_rooms):
        options = [discord.SelectOption(label=f"Room {i}", value=str(i)) for i in range(1, max_rooms + 1)]
        super().__init__(placeholder="Select the Room Instance / Selecione a Sub-sala", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.room_number = int(self.values[0])
        
        view.clear_items()
        view.add_item(TicketSelect(view.map_type, view.floor, view.spot))
        
        map_label = Config.MAP_DATA[view.map_type]['label']
        await interaction.response.edit_message(
            content=f"🗺️ Map: **{map_label}** | Floor: **{view.floor}** | Spot: **{view.spot}** | Room: **{view.room_number}**\n➡️ How many Tickets?",
            view=view
        )

class TicketSelect(discord.ui.Select):
    def __init__(self, map_type, floor, spot):
        spots_info = Config.MAP_DATA[map_type]["floors"][floor][spot]
        allowed_tickets = spots_info.get("tickets", list((1, 2, 3)))
        options = [discord.SelectOption(label=f"{t} Ticket(s)", value=str(t)) for t in allowed_tickets]
        super().__init__(placeholder="Select the Tickets / Quantidade de Tickets", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ClaimWizardView = self.view
        view.tickets = int(self.values[0])
        
        view.clear_items()
        await interaction.response.defer(ephemeral=True)
        
        # Formata o spot de forma limpa, bonita e em inglês para salvar no Banco de Dados
        map_label = "Magic Square" if view.map_type == "MAGIC_SQUARE" else "Secret Peak"
        spot_string = f"{map_label} {view.floor} - {view.spot} - Room {view.room_number} ({view.tickets} Tk)"
        
        # Registra a reivindicação de forma totalmente compatível com a sua arquitetura atual
        success = await view.bot.claim_service.register_claim(
            interaction.guild_id, interaction.user, spot_string
        )
        
        if success:
            await interaction.followup.send(
                f"✅ **Claim Successful!**\nYou successfully claimed: **{spot_string}**",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ **Claim Failed!**\nThe spot **{spot_string}** is already occupied or you already have an active claim in this map!",
                ephemeral=True
            )

class MIR4PanelPersistentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Claim Spot", style=discord.ButtonStyle.green, custom_id="mir4:btn_claim")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Abre o assistente dinâmico passo a passo em modo efêmero
        await interaction.response.send_message(
            content="🧙‍♂️ **MIR4 Claim Wizard starting...**\nSelect your destination below:",
            view=ClaimWizardView(self.bot),
            ephemeral=True
        )

    @discord.ui.button(label="Cancel Claim / Fila", style=discord.ButtonStyle.red, custom_id="mir4:btn_unclaim")
    async def unclaim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id

        claims = await self.bot.claim_repo.get_all_claims(guild_id)
        user_claims = [c for c in claims if c["user_id"] == interaction.user.id]

        if not user_claims:
            return await interaction.followup.send("⚠️ You do not have any active spots claimed.", ephemeral=True)

        for c in user_claims:
            await self.bot.claim_service.release_claim(guild_id, interaction.user, c["spot_name"])

        await interaction.followup.send("✅ Your active claims have been released
