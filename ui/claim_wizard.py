import discord
import aiosqlite # CORRIGIDO: Adicionada a importação que resolveu o NameError do log
from discord.ui import View, Button
from config import Config
from services.claim_service import ClaimService, DatabaseManager
from datetime import datetime, timedelta

class ClaimWizardView(View):
    def __init__(self, user: discord.User, map_type: str):
        super().__init__(timeout=60)
        self.user = user
        self.map_type = map_type
        self.floor = None
        self.spot_type = None
        self.room_number = None
        self.tickets = None
        self.is_queuing = False
        self._build_step_floor_selection()

    def _clear_items(self):
        for item in self.children.copy():
            self.remove_item(item)

    def _build_step_floor_selection(self):
        self._clear_items()
        floors = Config.MAP_DATA[self.map_type]["floors"].keys()
        for floor in floors:
            btn = Button(label=floor, style=discord.ButtonStyle.secondary, custom_id=f"f_{floor}")
            btn.callback = self.floor_callback
            self.add_item(btn)

    async def floor_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ Esta sessão não pertence a você.", ephemeral=True)
            
        self.floor = interaction.data["custom_id"].split("_")[1]
        self._clear_items()
        
        available_spots = Config.MAP_DATA[self.map_type]["floors"][self.floor].keys()
        for spot in available_spots:
            btn = Button(label=spot, style=discord.ButtonStyle.success, custom_id=f"s_{spot}")
            btn.callback = self.spot_callback
            self.add_item(btn)
            
        embed = discord.Embed(
            title=f"🎯 Alocação de Quadrante | {self.floor}",
            description="Selecione abaixo a coordenada geográfica ou alvo de farm planejado:",
            color=0x2ecc71
        )
        if self.map_type == "SECRET_PEAK":
            embed.set_image(url=Config.SECRET_PEAK_MAP_URL)
            
        await interaction.response.edit_message(embed=embed, view=self)

    async def spot_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ Esta sessão não pertence a você.", ephemeral=True)
            
        self.spot_type = interaction.data["custom_id"].split("_")[1]
        spot_info = Config.MAP_DATA[self.map_type]["floors"][self.floor][self.spot_type]
        
        # OTIMIZAÇÃO HISTÓRICA: Coleta todas as validações de uma vez só no banco para remover lag de clique
        vacant_room, empty_room, queue_count = await ClaimService.prepare_spot_interaction(
            self.map_type, self.floor, self.spot_type, spot_info["rooms"]
        )
        
        self._clear_items()
        
        if vacant_room:
            ends_at_dt = datetime.fromisoformat(vacant_room['ends_at'])
            remaining = ends_at_dt - datetime.utcnow()
            rem_mins = max(1, int(remaining.total_seconds() / 60))
            
            btn_vacant = Button(label=f"Assumir Tempo Restante ({rem_mins}m)", style=discord.ButtonStyle.success, custom_id=f"v_{vacant_room['id']}")
            btn_vacant.callback = self.claim_vacant_callback
            self.add_item(btn_vacant)
            
            embed = discord.Embed(
                title="♻️ Herança de Janela Remanescente",
                description=f"Existe um tempo restante livre de **{rem_mins} minutos**.\nDeseja herdar essa fração cronológica imediatamente?",
                color=0xe67e22
            )
            return await interaction.response.edit_message(embed=embed, view=self)
            
        if empty_room is None:
            if not spot_info["allow_queue"]:
                embed = discord.Embed(
                    title="⚡ Recurso Indisponível",
                    description=f"O spot **{self.spot_type}** está ocupado e as regras deste mapa proíbem filas de espera.",
                    color=0xe74c3c
                )
                return await interaction.response.edit_message(embed=embed, view=None)

            if queue_count >= Config.MAX_QUEUE_SIZE:
                embed = discord.Embed(
                    title="⛔ Lista de Espera Lotada",
                    description=f"O limite máximo de **{Config.MAX_QUEUE_SIZE} pessoas** na fila de espera foi atingido.",
                    color=0xe74c3c
                )
                return await interaction.response.edit_message(embed=embed, view=None)

            self.is_queuing = True
            for tk in spot_info["tickets"]:
                btn = Button(label=f"Fila: {tk} Ticket(s)", style=discord.ButtonStyle.primary, custom_id=f"t_{tk}")
                btn.callback = self.tickets_callback
                self.add_item(btn)
                
            embed = discord.Embed(title="👥 Entrar na Lista de Espera", description=f"Ocupação máxima atingida. Posições ocupadas: `{queue_count}/{Config.MAX_QUEUE_SIZE}`.", color=0xe67e22)
            return await interaction.response.edit_message(embed=embed, view=self)

        self.room_number = empty_room
        for tk in spot_info["tickets"]:
            btn = Button(label=f"{tk} Ticket(s) ({tk * 30}m)", style=discord.ButtonStyle.danger, custom_id=f"t_{tk}")
            btn.callback = self.tickets_callback
            self.add_item(btn)
            
        embed = discord.Embed(title="🎫 Seleção de Duração", description="Selecione quantos tickets de 30 minutos deseja gastar:", color=0x2ecc71)
        await interaction.response.edit_message(embed=embed, view=self)

    async def claim_vacant_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ Esta sessão não pertence a você.", ephemeral=True)
            
        claim_id = int(interaction.data["custom_id"].split("_")[1])
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row # CORRIGIDO: Módulo aiosqlite agora é reconhecido perfeitamente
            async with db.execute("SELECT * FROM claims WHERE id = ? AND status = 'VACANT_REMAINING'", (claim_id,)) as cursor:
                claim = await cursor.fetchone()
                
        if not claim:
            return await interaction.response.edit_message(content="❌ Vaga indisponível ou já reivindicada concorrentemente.", embed=None, view=None)
            
        await ClaimService.claim_vacant_remaining(claim_id, self.user.id, self.user.name)
        ends_at_dt = datetime.fromisoformat(claim['ends_at'])
        remaining = ends_at_dt - datetime.utcnow()
        rem_mins = max(1, int(remaining.total_seconds() / 60))
        
        server_end_time = ends_at_dt + timedelta(hours=Config.TIMEZONE_OFFSET)
        
        embed = discord.Embed(title="⚔️ Tempo Remanescente Assumido!", color=0x2ecc71)
        embed.add_field(name="🏢 Andar", value=claim['floor'], inline=True)
        embed.add_field(name="🎯 Spot", value=claim['spot_type'], inline=True)
        if self.map_type == "MAGIC_SQUARE":
            embed.add_field(name="🚪 Sub-Sala", value=f"Sala {claim['room_number']}", inline=True)
        embed.add_field(name="⏰ Horário de Saída", value=f"**{server_end_time.strftime('%H:%M')}**", inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
        
        await ClaimService.dispatch_admin_log(interaction.client, "HERANÇA", self.user, claim['map_type'], claim['floor'], claim['spot_type'], claim['room_number'], rem_mins)
        claim_cog = interaction.client.get_cog("ClaimCog")
        if claim_cog:
            await claim_cog.update_floor_dashboard(claim['map_type'], claim['floor'])
        self.stop()

    async def tickets_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ Esta sessão não pertence a você.", ephemeral=True)
            
        self.tickets = int(interaction.data["custom_id"].split("_")[1])
        spot_info = Config.MAP_DATA[self.map_type]["floors"][self.floor][self.spot_type]
        
        if self.is_queuing:
            inserted = await ClaimService.add_to_queue(self.user.id, self.user.name, self.map_type, self.floor, self.spot_type, self.tickets)
            if not inserted:
                return await interaction.response.edit_message(content="❌ Falha ao processar entrada na fila.", embed=None, view=None)
                
            embed = discord.Embed(title="✅ Posicionado na Lista de Espera", color=0xe67e22)
            embed.add_field(name="🏢 Andar", value=self.floor, inline=True)
            embed.add_field(name="🎯 Spot", value=self.spot_type, inline=True)
            await interaction.response.edit_message(embed=embed, view=None)
            
            await ClaimService.dispatch_admin_log(interaction.client, "QUEUE", self.user, self.map_type, self.floor, self.spot_type, 0, self.tickets * 30)
            claim_cog = interaction.client.get_cog("ClaimCog")
            if claim_cog:
                await claim_cog.update_floor_dashboard(self.map_type, self.floor)
            return self.stop()

        now_utc = datetime.utcnow()
        ends_at = await ClaimService.create_claim(self.user.id, self.user.name, self.map_type, self.floor, self.spot_type, self.room_number, self.tickets)
        
        server_start_time = now_utc + timedelta(hours=Config.TIMEZONE_OFFSET)
        server_end_time = ends_at + timedelta(hours=Config.TIMEZONE_OFFSET)
        
        embed = discord.Embed(title="⚔️ Alocação de Instância Concluída!", color=0x2ecc71)
        embed.add_field(name="🏢 Andar", value=self.floor, inline=True)
        embed.add_field(name="🎯 Spot Ativo", value=self.spot_type, inline=True)
        if self.map_type == "MAGIC_SQUARE":
            embed.add_field(name="🚪 Sub-Sala Fixada", value=f"Sala {self.room_number}", inline=True)
        embed.add_field(name="🎫 Consumo", value=f"{self.tickets} Ticket(s) ({self.tickets * 30}m)", inline=True)
        embed.add_field(name="⏰ Janela Cronológica", value=f"Início: **{server_start_time.strftime('%H:%M')}** ➔ Término: **{server_end_time.strftime('%H:%M')}**", inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
        
        await ClaimService.dispatch_admin_log(interaction.client, "CLAIM", self.user, self.map_type, self.floor, self.spot_type, self.room_number, self.tickets * 30)
        claim_cog = interaction.client.get_cog("ClaimCog")
        if claim_cog:
            await claim_cog.update_floor_dashboard(self.map_type, self.floor)
        self.stop()