import discord
from discord.ext import commands, tasks
from ui.main_panel import MainControlPanel
from ui.floor_events_view import FloorEventButtonsView
from services.claim_service import ClaimService, DatabaseManager
from config import Config
from datetime import datetime, timedelta
import aiosqlite

class ClaimCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dashboard_updater.start()

    def cog_unload(self):
        self.dashboard_updater.cancel()

    @commands.command(name="setup_ms_panel")
    @commands.has_permissions(administrator=True)
    async def setup_ms_panel(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🚀 PAINEL OPERACIONAL | PRAÇA MÁGICA",
            description=(
                "🇺🇸 **How to claim spot?**\n• Click on `Claim`;\n• Select floor and tickets.\n\n"
                "🇧🇷 **Como claimar um spot?**\n• Clique em `Claim`;\n• Selecione o andar e os tickets.\n\n"
                "🇪🇸 **Como seleccionar una locacion?**\n• Oprima en `Claim`;\n• Seleccione campos de tiempo."
            ),
            color=0x9b59b6
        )
        await ctx.send(embed=embed, view=MainControlPanel("MAGIC_SQUARE"))
        await ctx.message.delete()

    @commands.command(name="setup_ps_panel")
    @commands.has_permissions(administrator=True)
    async def setup_ps_panel(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🚀 PAINEL OPERACIONAL | PICO SECRETO",
            description=(
                "🇺🇸 **How to claim spot?**\n• Click on `Claim`;\n• Select floor and tickets.\n\n"
                "🇧🇷 **Como claimar um spot?**\n• Clique em `Claim`;\n• Selecione o andar e os tickets.\n\n"
                "🇪🇸 **Como seleccionar una locacion?**\n• Oprima en `Claim`;\n• Seleccione campos de tempo."
            ),
            color=0xe67e22
        )
        await ctx.send(embed=embed, view=MainControlPanel("SECRET_PEAK"))
        await ctx.message.delete()

    def _calculate_next_fixed_boss(self, map_type: str, floor: str, boss_type: str) -> tuple:
        now_server = datetime.utcnow() + timedelta(hours=Config.TIMEZONE_OFFSET)
        
        map_schedule = Config.FIXED_BOSS_HOURS.get(map_type, {})
        if floor in map_schedule:
            target_times = map_schedule[floor].get(boss_type, [])
        else:
            target_times = map_schedule.get("DEFAULT", {}).get(boss_type, [])
            
        if not target_times:
            return "--:--", "--", -1
        
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
        return next_target.strftime("%H:%M"), rem_str, total_mins

    async def check_and_process_queue(self, map_type: str, floor: str, spot_type: str, room_number: int):
        spot_info = Config.MAP_DATA[map_type]["floors"][floor][spot_type]
        if not spot_info["allow_queue"]:
            await self.update_floor_dashboard(map_type, floor)
            return

        next_user = await ClaimService.get_next_in_queue(map_type, floor, spot_type)
        if next_user:
            await ClaimService.remove_from_queue(next_user['id'])
            await ClaimService.create_claim(next_user['user_id'], next_user['username'], map_type, floor, spot_type, room_number, next_user['tickets'])
            try:
                discord_user = await self.bot.fetch_user(next_user['user_id'])
                if discord_user:
                    await ClaimService.dispatch_admin_log(self.bot, "CLAIM", discord_user, map_type, floor, spot_type, room_number, next_user['tickets'] * 30)
                    await discord_user.send(f"⚔️ Sua vez chegou! Você foi movido automaticamente para o **{floor} - {spot_type}**.")
            except:
                pass
        await self.update_floor_dashboard(map_type, floor)

    async def update_floor_dashboard(self, map_type: str, current_floor: str):
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM floor_dashboards WHERE map_type = ? AND floor = ?", (map_type, current_floor)) as cursor:
                dash = await cursor.fetchone()
            if not dash:
                return
            channel = self.bot.get_channel(dash['channel_id'])
            if not channel:
                return
                
            map_label = Config.MAP_DATA[map_type]["label"]
            embed = discord.Embed(title=f"{map_label} | {current_floor}", color=0x9b59b6 if map_type == "MAGIC_SQUARE" else 0xe67e22)
            
            # LIVE STATUS TAPE (TICKER) - APENAS RENDERIZAÇÃO VISUAL NO EMBED (SEM PINGS DE SPAM)
            if map_type == "SECRET_PEAK":
                sul_time, sul_rem, sul_mins = self._calculate_next_fixed_boss("SECRET_PEAK", current_floor, "SUL")
                norte_time, norte_rem, norte_mins = self._calculate_next_fixed_boss("SECRET_PEAK", current_floor, "NORTE")
                ticker_line = f"🕒 **[SUL]** Respawn às `{sul_time}` (Falta **{sul_rem}**)\n🕒 **[NORTE]** Respawn às `{norte_time}` (Falta **{norte_rem}**)"
                embed.add_field(name="📊 LIVE STATUS TAPE | TIMERS FIXOS DO PICO", value=ticker_line, inline=False)

            elif map_type == "MAGIC_SQUARE":
                l3_time, l3_rem, l3_mins = self._calculate_next_fixed_boss("MAGIC_SQUARE", current_floor, "LÍDER_3")
                ticker_lines = [f"👑 **[LÍDER 3]** Respawn às `{l3_time}` (Falta **{l3_rem}**)"]
                
                if current_floor in ["11F", "12F"]:
                    furia_time, furia_rem, furia_mins = self._calculate_next_fixed_boss("MAGIC_SQUARE", current_floor, "FÚRIA")
                    frenzy_time, frenzy_rem, frenzy_mins = self._calculate_next_fixed_boss("MAGIC_SQUARE", current_floor, "FRENZY")
                    ticker_lines.append(f"⚡ **[FÚRIA]** Próxima sala às `{furia_time}` (Falta **{furia_rem}**)")
                    ticker_lines.append(f"🔥 **[FRENZY]** Próxima sala às `{frenzy_time}` (Falta **{frenzy_rem}**)")
                                
                embed.add_field(name="📊 LIVE STATUS TAPE | COMPUTAÇÃO DE TIMERS DA PRAÇA", value="\n".join(ticker_lines), inline=False)

            # SEÇÃO 2: CRONÔMETROS DIGITADOS PELO LÍDER DO BOSS
            event_rows = await ClaimService.get_floor_events(map_type, current_floor)
            valid_keys = Config.get_valid_events_for_floor(map_type, current_floor)
            
            activity_lines = []
            for row in event_rows:
                evt_key = row['event_name']
                if evt_key not in valid_keys:
                    continue
                    
                evt_config = Config.TRACKABLE_EVENTS[map_type][evt_key]
                time_display = f"**{(datetime.fromisoformat(row['last_triggered_at']) + timedelta(hours=Config.TIMEZONE_OFFSET)).strftime('%H:%M')}**" if row['last_triggered_at'] else "`--:--`"
                activity_lines.append(f"{evt_config['emoji']} **{evt_config['label']}:** {time_display}")
                
            if activity_lines:
                embed.add_field(name="📋 Horários de Respawn / Rotação", value="\n".join(activity_lines), inline=False)
            
            embed.add_field(name="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", value="**🛡️ MONITORAMENTO DE RECURSOS ATIVOS**", inline=False)

            floor_spots = Config.MAP_DATA[map_type]["floors"].get(current_floor, {})
            for spot, info in floor_spots.items():
                max_rooms = info["rooms"]
                spot_emoji = info["emoji"]
                allow_queue = info["allow_queue"]
                
                async with db.execute("SELECT * FROM claims WHERE map_type = ? AND floor = ? AND spot_type = ? AND status IN ('ACTIVE', 'VACANT_REMAINING')", (map_type, current_floor, spot)) as c_cursor:
                    active_claims = await c_cursor.fetchall()
                
                claims_by_room = {c['room_number']: c for c in active_claims}
                queue_list = await ClaimService.get_queue_list(map_type, current_floor, spot) if allow_queue else []
                
                queue_text = f"\n👥 **Fila (`{len(queue_list)}/{Config.MAX_QUEUE_SIZE}`):** " + ", ".join([f"<@{q['user_id']}>" for q in queue_list]) if queue_list else ""

                if max_rooms == 1:
                    spot_header = f"{spot_emoji} **{spot}**"
                    if 1 in claims_by_room:
                        c = claims_by_room[1]
                        start_time = datetime.fromisoformat(c['started_at']) + timedelta(hours=Config.TIMEZONE_OFFSET)
                        end_time = datetime.fromisoformat(c['ends_at']) + timedelta(hours=Config.TIMEZONE_OFFSET)
                        
                        if c['status'] == 'VACANT_REMAINING':
                            status_text = f"🟢 **Tempo Restante** | `Até {end_time.strftime('%H:%M')}`"
                        else:
                            status_text = f"🔴 <@{c['user_id']}> (`{start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}`)"
                        status_text += queue_text
                    else:
                        status_text = f"🟢 Disponível"
                    
                    use_inline = map_type == "SECRET_PEAK" and spot not in ["SUMMON GOBLIN", "SUMMON EVENTS", "BOSS"]
                    embed.add_field(name=spot_header, value=status_text, inline=use_inline)
                else:
                    spot_header = f"{spot_emoji} **{spot} ({max_rooms} Salas)**"
                    status_lines = []
                    for room_no in range(1, max_rooms + 1):
                        if room_no in claims_by_room:
                            c = claims_by_room[room_no]
                            start_time = datetime.fromisoformat(c['started_at']) + timedelta(hours=Config.TIMEZONE_OFFSET)
                            end_time = datetime.fromisoformat(c['ends_at']) + timedelta(hours=Config.TIMEZONE_OFFSET)
                            if c['status'] == 'VACANT_REMAINING':
                                status_lines.append(f"🔹 Sala {room_no}: 🟢 **Tempo Restante** | `Até {end_time.strftime('%H:%M')}`")
                            else:
                                status_lines.append(f"🔹 Sala {room_no}: 🔴 <@{c['user_id']}> (`{start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}`)")
                        else:
                            status_lines.append(f"🔹 Sala {room_no}: 🟢 Disponível")
                    if queue_text:
                        status_lines.append(queue_text)
                    embed.add_field(name=spot_header, value="\n".join(status_lines), inline=False)
            
            view_component = FloorEventButtonsView(map_type, current_floor)
            try:
                msg = await channel.fetch_message(dash['message_id'])
                await msg.edit(embed=embed, view=view_component)
            except:
                msg = await channel.send(embed=embed, view=view_component)
                await db.execute("UPDATE floor_dashboards SET message_id = ? WHERE map_type = ? AND floor = ?", (msg.id, map_type, current_floor))
                await db.commit()

    @tasks.loop(seconds=15)
    async def dashboard_updater(self):
        now = datetime.utcnow()
        expired_claims = []
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM claims WHERE status IN ('ACTIVE', 'VACANT_REMAINING') AND datetime(ends_at) <= datetime(?)", (now.isoformat(),)) as cursor:
                expired_claims = await cursor.fetchall()
            if expired_claims:
                await db.execute("UPDATE claims SET status = 'EXPIRED' WHERE status IN ('ACTIVE', 'VACANT_REMAINING') AND datetime(ends_at) <= datetime(?)", (now.isoformat(),))
                await db.commit()

        for claim in expired_claims:
            try:
                fake_user = type('User', (object,), {'mention': f"<@{claim['user_id']}>", 'name': claim['username']})
                await ClaimService.dispatch_admin_log(self.bot, "EXPIRED", fake_user, claim['map_type'], claim['floor'], claim['spot_type'], claim['room_number'])
            except:
                pass
            await self.check_and_process_queue(claim['map_type'], claim['floor'], claim['spot_type'], claim['room_number'])

        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT map_type, floor FROM floor_dashboards") as cursor:
                floors = await cursor.fetchall()
        for row in floors:
            await self.update_floor_dashboard(row['map_type'], row['floor'])

    @dashboard_updater.before_loop
    async def before_dashboard_updater(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(ClaimCog(bot))
