import discord
import aiosqlite
from discord.ui import View, Button
from ui.claim_wizard import ClaimWizardView
from services.claim_service import ClaimService, DatabaseManager
from config import Config

class MainControlPanel(View):
    def __init__(self, map_type: str):
        super().__init__(timeout=None)
        self.map_type = map_type

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, custom_id="persistent_claim_btn")
    async def claim_button(self, interaction: discord.Interaction, button: Button):
        # Validação isolada de concorrência por contexto de mapa ativo
        has_claim, in_queue = await ClaimService.check_user_status(interaction.user.id, self.map_type)
        
        if has_claim:
            return await interaction.response.send_message(
                f"❌ Você já possui uma conta alocada em **{Config.MAP_DATA[self.map_type]['label']}**. Finalize-a antes de redefinir.", 
                ephemeral=True
            )
            
        if in_queue:
            return await interaction.response.send_message(
                f"❌ Você já se encontra posicionado em uma lista de espera ativa dentro de **{Config.MAP_DATA[self.map_type]['label']}**.", 
                ephemeral=True
            )
            
        # O MAPA É INVOCADO EXCLUSIVAMENTE NA VIEW PRIVADA EFÊMERA (ANTI-POLUIÇÃO)
        if self.map_type == "SECRET_PEAK":
            embed = discord.Embed(
                title="🏔️ Pico Secreto | Central de Alocações",
                description="Selecione abaixo o andar de destino. Utilize o mapa de suporte anexado abaixo para se localizar geograficamente:",
                color=0xe67e22
            )
            embed.set_image(url=Config.SECRET_PEAK_MAP_URL)
        else:
            embed = discord.Embed(
                title="🔮 Praça Mágica | Central de Alocações",
                description="Selecione abaixo o andar alvo para prosseguir com a reserva automatizada de sub-salas:",
                color=0x9b59b6
            )
            
        wizard = ClaimWizardView(interaction.user, self.map_type)
        await interaction.response.send_message(embed=embed, view=wizard, ephemeral=True)

    @discord.ui.button(label="Cancel Claim / Fila", style=discord.ButtonStyle.danger, custom_id="persistent_cancel_btn")
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        success, map_type, floor, spot_type, room_number, was_vacated = await ClaimService.cancel_active_claim(interaction.user.id, self.map_type)
        
        if success:
            await interaction.response.send_message("✅ Sua alocação ativa neste mapa foi cancelada e limpa!", ephemeral=True)
            await ClaimService.dispatch_admin_log(interaction.client, "CANCEL", interaction.user, map_type, floor, spot_type, room_number)
            claim_cog = interaction.client.get_cog("ClaimCog")
            if claim_cog:
                await claim_cog.update_floor_dashboard(map_type, floor)
            return

        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM spot_queues WHERE user_id = ? AND map_type = ?", (interaction.user.id, self.map_type)) as cursor:
                queue_data = await cursor.fetchone()
                
        if queue_data:
            await ClaimService.remove_from_queue(queue_data['id'])
            await interaction.response.send_message("✅ Você removeu seu ID da fila de espera de forma voluntária.", ephemeral=True)
            await ClaimService.dispatch_admin_log(interaction.client, "CANCEL", interaction.user, queue_data['map_type'], queue_data['floor'], queue_data['spot_type'], 0)
            claim_cog = interaction.client.get_cog("ClaimCog")
            if claim_cog:
                await claim_cog.update_floor_dashboard(queue_data['map_type'], queue_data['floor'])
        else:
            await interaction.response.send_message("❌ Você não possui registros de claims ativos ou filas neste mapa específico.", ephemeral=True)