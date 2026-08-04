import discord
from typing import Optional
from services.claim_service import claim_service
from config import logger

class MainControlPanel(discord.ui.View):
    def __init__(self, message: Optional[discord.Message] = None):
        super().__init__(timeout=None)
        self.message = message
        claim_service.register_panel(self)

    async def refresh_panel(self):
        if self.message:
            try:
                embed = self.generate_status_embed()
                await self.message.edit(embed=embed, view=self)
            except Exception as e:
                logger.error(f"Failed to edit panel message: {e}")

    def generate_status_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🛸 MIR4 MARS - Control Panel (Square & Peak Claims)",
            description="Real-time synchronized portal monitoring system.\nUse the buttons below to manage your claims.",
            color=discord.Color.gold()
        )
        claims = claim_service.get_all_claims()
        
        sq_claims = [v for k, v in claims.items() if k.startswith("Square")]
        pk_claims = [v for k, v in claims.items() if k.startswith("Peak")]

        sq_text = "".join([f"• **{c['floor']}** - `{c['room']}`: {c['user_name']}" + (" 🎟️ [EXTRA]" if c.get("extra_ticket") else "") + (" ⚡ [EARLY]" if c.get("early_mode") else "") + "\n" for c in sq_claims])
        pk_text = "".join([f"• **{c['floor']}** - `{c['room']}`: {c['user_name']}" + (" 🎟️ [EXTRA]" if c.get("extra_ticket") else "") + (" ⚡ [EARLY]" if c.get("early_mode") else "") + "\n" for c in pk_claims])

        embed.add_field(name="🔮 Magic Square Claims", value=sq_text if sq_text else "*No active claims*", inline=False)
        embed.add_field(name="🏔️ Secret Peak Claims", value=pk_text if pk_text else "*No active claims*", inline=False)
        embed.set_footer(text="Synchronized Active Instance • Render Engine")
        return embed

    @discord.ui.button(label="Claim Room", style=discord.ButtonStyle.primary, custom_id="mars_btn_claim", emoji="📝")
    async def btn_claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.claim_wizard import ZoneSelectView
        await interaction.response.send_message("Select the zone you wish to claim:", view=ZoneSelectView(), ephemeral=True)

    @discord.ui.button(label="Extra Ticket / Early Mode", style=discord.ButtonStyle.secondary, custom_id="mars_btn_frenzy", emoji="🎟️")
    async def btn_frenzy(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.claim_wizard import FrenzyTicketView
        await interaction.response.send_message("⚡ **Frenzy/Fury Ticket System**\nSelect your claim mode:", view=FrenzyTicketView(), ephemeral=True)

    @discord.ui.button(label="Refresh Panels", style=discord.ButtonStyle.success, custom_id="mars_btn_refresh", emoji="🔄")
    async def btn_refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await claim_service.sync_all_panels()
        await interaction.response.send_message("All active panels synchronized successfully.", ephemeral=True)
