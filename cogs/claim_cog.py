import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
from datetime import datetime, timedelta
from config import Config, logger
from database.connection import DatabaseManager
from services.claim_service import ClaimService

class ClaimCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dashboard_updater.start()

    def cog_unload(self):
        self.dashboard_updater.cancel()

    def calculate_ticker_line(self, map_type: str, floor: str) -> str:
        now_server = datetime.utcnow() + timedelta(hours=Config.TIMEZONE_OFFSET)
        map_schedule = Config.FIXED_BOSS_HOURS.get(map_type, {})
        
        if floor in map_schedule:
            schedule = map_schedule[floor]
        else:
            schedule = map_schedule.get("DEFAULT", {})

        if not schedule:
            return ""

        ticker_lines = []
        for boss_key, target_times in schedule.items():
            if not target_times:
                continue
            
            next_target = None
            for time_str in target_times:
                h, m = map(int, time_str.split(":"))
                target_dt = now_server.replace(hour=h, minute=m, second=0, microsecond=0)
                if target_dt > now_server:
                    next_target = target_dt
                    break
            
            if not next_target:
                h, m = map(int, target_times[0].split(":"))
                next_target = now_server.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(days=1)

            diff = next_target - now_server
            total_mins = int(diff.total_seconds() / 60)
            hours_rem = total_mins // 60
            mins_rem = total_mins % 60
            rem_str = f"{hours_rem}h {mins_rem}m" if hours_rem > 0 else f"{mins_rem}m"

            emoji = "👑" if boss_key == "LEADER_3" else "⚡" if boss_key == "FURY" else "🔥" if boss_key == "FRENZY" else "🕒"
            label = "LÍDER 3" if boss_key == "LEADER_3" else boss_key
            ticker_lines.append(f"{emoji} **[{label}]** Respawn às {next_target.strftime('%H:%M')} (Falta **{rem_str}**)")

        return "\n".join(ticker_lines)

    async def check_and_process_queue(self, guild_id: int, map_type: str, floor: str, spot_type: str, room_number: int):
        spot_info = Config.MAP_DATA[map_type]["floors"][floor][spot_type]
        if not spot_info.get("allow_queue", True):
            await self.bot.panel_service.update_floor_dashboard(guild_id, map_type, floor)
            return

        next_user = await ClaimService.get_next_in_queue(map_type, floor, spot_type)
        if next_user:
            await ClaimService.remove_from_queue(next_user['id'])
            await ClaimService.create_claim(guild_id, next_user['user_id'], next_user['username'], map_type, floor, spot_type, room_number, next_user['tickets'])
            try:
                discord_user = await self.bot.fetch_user(next_user['user_id'])
                if discord_user:
                    await self.bot.log_service.dispatch_claim_log(guild_id, discord_user, map_type, floor, spot_type, room_number, "CLAIM", f"Fila ativada: {next_user['tickets']} Tickets")
                    await discord_user.send(f"⚔️ **Sua vez chegou!** Você foi alocado automaticamente no spot `{floor} - {spot_type}` (Sala {room_number}).")
            except:
                pass
        await self.bot.panel_service.update_floor_dashboard(guild_id, map_type, floor)

    @tasks.loop(seconds=15)
    async def dashboard_updater(self):
        now = datetime.utcnow()
        expired_claims = []
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM claims WHERE status IN ('ACTIVE', 'VACANT_REMAINING') AND datetime(ends_at) <= datetime(?)",
                (now.isoformat(),)
            ) as cursor:
                expired_claims = [dict(r) for r in await cursor.fetchall()]

            if expired_claims:
                await db.execute(
                    "UPDATE claims SET status = 'EXPIRED' WHERE status IN ('ACTIVE', 'VACANT_REMAINING') AND datetime(ends_at) <= datetime(?)",
                    (now.isoformat(),)
                )
                await db.commit()

        for claim in expired_claims:
            guild_id = claim["guild_id"]
            try:
                fake_user = type('User', (object,), {'mention': f"<@{claim['user_id']}>", 'name': claim['username'], 'display_name': claim['username']})
                await self.bot.log_service.dispatch_claim_log(guild_id, fake_user, claim['map_type'], claim['floor'], claim['spot_type'], claim['room_number'], "EXPIRED")
            except:
                pass
            await self.check_and_process_queue(guild_id, claim['map_type'], claim['floor'], claim['spot_type'], claim['room_number'])

        active_dashboards = []
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT guild_id, map_type, floor FROM floor_dashboards") as cursor:
                active_dashboards = [dict(r) for r in await cursor.fetchall()]

        for d in active_dashboards:
            try:
                await self.bot.panel_service.update_floor_dashboard(d["guild_id"], d["map_type"], d["floor"])
            except Exception as e:
                logger.error(f"Erro ao atualizar dashboard {d['map_type']} {d['floor']}: {e}")

    @dashboard_updater.before_loop
    async def before_dashboard_updater(self):
        await self.bot.wait_until_ready()

    @app_commands.command(
        name="setup_painel",
        description="Configura um painel de claims (canal de cliques) ou placar de andar (canal de placar)."
    )
    @app_commands.describe(
        map_type="Selecione o mapa para este painel",
        floor="Selecione o andar se for criar um placar de andar, ou deixe em branco para o painel de claims principal"
    )
    @app_commands.choices(
        map_type=[
            app_commands.Choice(name="🔮 Praça Mágica", value="MAGIC_SQUARE"),
            app_commands.Choice(name="🏔️ Pico Secreto", value="SECRET_PEAK")
        ],
        floor=[
            app_commands.Choice(name="6F", value="6F"),
            app_commands.Choice(name="7F", value="7F"),
            app_commands.Choice(name="8F", value="8F"),
            app_commands.Choice(name="9F", value="9F"),
            app_commands.Choice(name="10F", value="10F"),
            app_commands.Choice(name="11F", value="11F"),
            app_commands.Choice(name="12F", value="12F")
        ]
    )
    @commands.has_permissions(administrator=True)
    async def setup_painel(self, interaction: discord.Interaction, map_type: str, floor: str = None):
        await interaction.response.defer(ephemeral=True)
        floor_key = floor if floor else ""
        
        if floor_key:
            await self.bot.panel_service.update_floor_dashboard(
                guild_id=interaction.guild_id,
                map_type=map_type,
                floor=floor_key,
                target_channel=interaction.channel
            )
            msg = f"✅ Placar de monitoramento em tempo real de **{map_type} - {floor_key}** ativado!"
        else:
            await self.bot.panel_service.update_static_panel(
                guild_id=interaction.guild_id,
                map_type=map_type,
                target_channel=interaction.channel
            )
            msg = f"✅ Painel de claims principal de **{map_type}** ativado!"
            
        await interaction.followup.send(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClaimCog(bot))
