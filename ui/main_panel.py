import discord
from typing import Optional
from services.claim_service import claim_service
from ui.claim_wizard import ZoneSelectView
from config import logger

class MainControlPanel(discord.ui.View):
    def __init__(self, message: Optional[discord.Message] = None):
        # timeout=None é obrigatório para ser persistente
        super().__init__(timeout=None)
        self.message = message
        claim_service.register_panel(self)

    async def refresh_panel(self):
        if self.message:
            try:
                embed = self.generate_status_embed()
                await self.message.edit(embed=embed, view=self)
            except Exception as e:
                logger.error(f"Erro ao atualizar mensagem do painel: {e}")

    def generate_status_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🚀 PAINEL OPERACIONAL | PRAÇA MÁGICA & PICO",
            description=(
                "🇺🇸 **How to claim spot?**\n• Click on `Claim` and select floor/tickets.\n\n"
                "🇧🇷 **Como claimar um spot?**\n• Clique em `Claim` e selecione o andar/tickets.\n\n"
                "🇪🇸 **¿Cómo seleccionar una locación?**\n• Oprima en `Claim` y seleccione tiempo."
            ),
            color=discord.Color.from_rgb(46, 204, 113)
        )
        claims = claim_service.get_all_claims()
        
        sq_claims = [v for k, v in claims.items() if k.startswith("Square")]
        pk_claims = [v for k, v in claims.items() if k.startswith("Peak")]

        sq_text = "".join([f"• **{c['floor']}** - `{c['room']}`: {c['user_name']}\n" for c in sq_claims])
        pk_text = "".join([f"• **{c['floor']}** - `{c['room']}`: {c['user_name']}\n" for c in pk_claims])

        embed.add_field(name="🔮 Magic Square Active Claims", value=sq_text if sq_text else "*Nenhum spot ocupado*", inline=False)
        embed.add_field(name="🏔️ Secret Peak Active Claims", value=pk_text if pk_text else "*Nenhum spot ocupado*", inline=False)
        embed.set_footer(text="MIR4 MARS Engine • Persistent Sync Active")
        return embed

    # custom_id estático para responder ao clique mesmo após reinicialização
    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, custom_id="mars_btn_persistent_claim", emoji="📝")
    async def btn_claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_message(
                content="Select Zone / Selecione a Zona:",
                view=ZoneSelectView(),
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Erro no botão de claim: {e}")

    @discord.ui.button(label="Cancel Claim / Fila", style=discord.ButtonStyle.danger, custom_id="mars_btn_persistent_cancel", emoji="✖️")
    async def btn_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            released_count = await claim_service.release_user_claims(interaction.user.id)
            if released_count > 0:
                await interaction.response.send_message(
                    content=f"✅ {released_count} claim(s) cancelado(s) com sucesso!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    content="❌ Você não possui nenhum spot claimado ativo.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Erro no botão de cancelar: {e}")
