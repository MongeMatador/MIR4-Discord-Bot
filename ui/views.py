import discord

class SpotSelectModal(discord.ui.Modal, title="Reivindicar Spot MIR4"):
    spot_name = discord.ui.TextInput(
        label="Nome do Spot",
        placeholder="Ex: Praça 1 - Ouro, Pico 2 - Boss...",
        required=True,
        max_length=50
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        spot = self.spot_name.value.strip()

        success = await self.bot.claim_service.register_claim(
            interaction.guild_id, interaction.user, spot
        )

        if success:
            await interaction.followup.send(f"✅ Você assumiu o spot **{spot}**!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ O spot **{spot}** já está ocupado!", ephemeral=True)


class MIR4PanelPersistentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Reivindicar Spot", style=discord.ButtonStyle.green, custom_id="mir4:btn_claim")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SpotSelectModal(self.bot))

    @discord.ui.button(label="Liberar Meu Spot", style=discord.ButtonStyle.red, custom_id="mir4:btn_unclaim")
    async def unclaim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id

        claims = await self.bot.claim_repo.get_all_claims(guild_id)
        user_claims = [c for c in claims if c["user_id"] == interaction.user.id]

        if not user_claims:
            return await interaction.followup.send("⚠️ Você não possui spots ocupados.", ephemeral=True)

        for c in user_claims:
            await self.bot.claim_service.release_claim(guild_id, interaction.user, c["spot_name"])

        await interaction.followup.send("✅ Seu spot foi liberado!", ephemeral=True)

    @discord.ui.button(label="Atualizar", style=discord.ButtonStyle.secondary, custom_id="mir4:btn_refresh")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.bot.panel_service.update_panel(interaction.guild_id)
        await interaction.followup.send("🔄 Painel sincronizado!", ephemeral=True)
