import discord
from discord.ext import commands
from services.claim_service import ClaimService, DatabaseManager
from config import Config
import aiosqlite

class SOSResolveView(discord.ui.View):
    def __init__(self, original_author_id: int):
        super().__init__(timeout=None) # Botão duradouro e persistente
        self.original_author_id = original_author_id

    @discord.ui.button(label="🟢 Resolver Combate", style=discord.ButtonStyle.success, custom_id="resolve_sos_btn")
    async def resolve_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Validação de Segurança: Apenas quem tem cargo administrativo pode encerrar
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas generais ou administradores podem encerrar esta convocação.", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.color = 0x2ecc71 # Altera a cor do card para Verde (Sucesso)
        embed.title = "🟢 CONVOCAÇÃO DE GUERRA ENCERRADA"
        embed.description = f"~~{embed.description}~~\n\n✅ **Batalha encerrada!** A situação foi resolvida pelos nossos generais e o servidor voltou ao controle."
        embed.set_footer(text="Guerra Encerrada • MIR4 OS")
        
        # Remove os botões de ação do post para manter o chat limpo
        await interaction.response.edit_message(content="✅ **Convocação finalizada com sucesso!**", embed=embed, view=None)


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_sos_message_id = None
        self.active_sos_channel_id = None

    @commands.command(name="set_log_channel")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx: commands.Context, map_type: str, channel: discord.TextChannel):
        """Define o canal de logs/auditoria para um mapa específico"""
        map_type = map_type.upper()
        if map_type not in ["MAGIC_SQUARE", "SECRET_PEAK"]:
            await ctx.send("❌ Mapa inválido. Use `MAGIC_SQUARE` ou `SECRET_PEAK`.")
            return

        async with DatabaseManager.get_connection() as db:
            await db.execute(
                "INSERT OR REPLACE INTO log_channels (map_type, channel_id) VALUES (?, ?)",
                (map_type, channel.id)
            )
            await db.commit()
        
        await ctx.send(f"✅ Canal de logs para **{map_type}** definido em {channel.mention}.")

    @commands.command(name="link_floor")
    @commands.has_permissions(administrator=True)
    async def link_floor(self, ctx: commands.Context, map_type: str, floor: str, channel: discord.TextChannel):
        """Vincula um andar específico a um canal do Discord para exibir o dashboard"""
        map_type = map_type.upper()
        floor = floor.upper()

        if map_type not in Config.MAP_DATA:
            await ctx.send("❌ Mapa inválido. Use `MAGIC_SQUARE` ou `SECRET_PEAK`.")
            return

        if floor not in Config.MAP_DATA[map_type]["floors"]:
            await ctx.send(f"❌ Andar inválido para este mapa. Opções: {', '.join(Config.MAP_DATA[map_type]['floors'].keys())}")
            return

        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM floor_dashboards WHERE map_type = ? AND floor = ?",
                (map_type, floor)
            ) as cursor:
                row = await cursor.fetchone()

            if row:
                try:
                    old_channel = self.bot.get_channel(row['channel_id'])
                    if old_channel:
                        old_msg = await old_channel.fetch_message(row['message_id'])
                        await old_msg.delete()
                except:
                    pass

                await db.execute(
                    "UPDATE floor_dashboards SET channel_id = ?, message_id = NULL WHERE map_type = ? AND floor = ?",
                    (channel.id, map_type, floor)
                )
            else:
                await db.execute(
                    "INSERT INTO floor_dashboards (map_type, floor, channel_id, message_id) VALUES (?, ?, ?, NULL)",
                    (map_type, floor, channel.id)
                )
            await db.commit()

        await ctx.send(f"✅ Dashboard do **{map_type} - {floor}** vinculado ao canal {channel.mention}.")
        
        claim_cog = self.bot.get_cog("ClaimCog")
        if claim_cog:
            await claim_cog.update_floor_dashboard(map_type, floor)

    @commands.command(name="sos")
    @commands.has_permissions(administrator=True)
    async def global_sos(self, ctx: commands.Context, *, mensagem: str):
        """
        Comando exclusivo de administração para convocar a guilda inteira para guerra.
        Uso: !sos [Detalhes do combate, local, clã rival]
        """
        # Deleta a mensagem do comando para manter o chat tático
        await ctx.message.delete()
        
        embed = discord.Embed(
            title="🚨 CONVOCAÇÃO GERAL DE GUERRA 🚨",
            description=(
                f"**O Líder {ctx.author.mention} convocou todos para a batalha!**\n\n"
                f"**Situação / Local:**\n👉 *{mensagem}*\n\n"
                "⚠️ **Ação Requerida:** Parem o que estiverem fazendo e entrem na call de voz imediatamente!"
            ),
            color=0xff0000 # Vermelho Alerta
        )
        embed.set_footer(text="Guerra Ativa • MIR4 OS")
        embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/vL0_5qZ8GidH60WfFp9_2Zc_X2p1K7Tf2o7R_bZ0O6U/https/cdn.discordapp.com/emojis/889053894437433364.png")
        
        view = SOSResolveView(ctx.author.id)
        msg = await ctx.send(content="@everyone ⚔️ **FECHEM AS FILEIRAS! ENTRAR EM CALL AGORA!** ⚔️", embed=embed, view=view)
        
        # Armazena na memória volátil do bot para permitir a edição posterior
        self.active_sos_message_id = msg.id
        self.active_sos_channel_id = ctx.channel.id

    @commands.command(name="update_sos")
    @commands.has_permissions(administrator=True)
    async def update_sos(self, ctx: commands.Context, *, nova_mensagem: str):
        """
        Edita o SOS ativo no servidor para atualizar a localização sem gerar novo ping de spam.
        Uso: !update_sos [Nova Situação/Localização]
        """
        await ctx.message.delete()
        
        if not self.active_sos_message_id or not self.active_sos_channel_id:
            await ctx.send("❌ Não há nenhuma convocação de SOS ativa no momento para ser atualizada.", delete_after=5)
            return
            
        try:
            channel = self.bot.get_channel(self.active_sos_channel_id)
            msg = await channel.fetch_message(self.active_sos_message_id)
            
            embed = msg.embeds[0]
            embed.description = (
                f"**Convocação de Batalha Ativa!**\n\n"
                f"**Situação Atualizada / Novo Local:**\n👉 *{nova_mensagem}*\n\n"
                "⚠️ **Ação Requerida:** Desloquem-se para as novas coordenadas imediatamente!"
            )
            embed.color = 0xe74c3c # Laranja Alerta (Indica atualização)
            embed.set_footer(text="Guerra Atualizada • MIR4 OS")
            
            await msg.edit(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao tentar atualizar o SOS: {str(e)}", delete_after=5)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
