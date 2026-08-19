import discord
import aiosqlite
from database.connection import DatabaseManager
from ui.embeds import MIR4Embeds
from config import Config, logger

class PanelService:
    def __init__(self, bot):
        self.bot = bot

    async def update_static_panel(self, guild_id: int, map_type: str, target_channel: discord.TextChannel = None):
        from ui.views import MIR4MSPanelPersistentView, MIR4PSPanelPersistentView
        
        embed = MIR4Embeds.build_panel_embed(map_type)
        view = MIR4MSPanelPersistentView(self.bot) if map_type == "MAGIC_SQUARE" else MIR4PSPanelPersistentView(self.bot)

        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT channel_id, message_id FROM panel_settings WHERE guild_id = ? AND map_type = ?",
                (guild_id, map_type)
            ) as cursor:
                row = await cursor.fetchone()

        if row:
            channel = self.bot.get_channel(row["channel_id"])
            if channel:
                try:
                    msg = await channel.fetch_message(row["message_id"])
                    await msg.edit(embed=embed, view=view)
                    return
                except discord.NotFound:
                    pass

        dest_channel = target_channel
        if dest_channel:
            new_msg = await dest_channel.send(embed=embed, view=view)
            async with DatabaseManager.get_connection() as db:
                await db.execute("""
                    INSERT INTO panel_settings (guild_id, map_type, channel_id, message_id)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(guild_id, map_type) DO UPDATE SET
                        channel_id = excluded.channel_id,
                        message_id = excluded.message_id
                """, (guild_id, map_type, dest_channel.id, new_msg.id))
                await db.commit()

    async def update_floor_dashboard(self, guild_id: int, map_type: str, floor: str, target_channel: discord.TextChannel = None):
        from ui.views import FloorEventButtonsView
        
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT channel_id, message_id FROM floor_dashboards WHERE guild_id = ? AND map_type = ? AND floor = ?",
                (guild_id, map_type, floor)
            ) as cursor:
                row = await cursor.fetchone()

        if not row and not target_channel:
            return

        claims = []
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM claims WHERE guild_id = ? AND map_type = ? AND floor = ? AND status IN ('ACTIVE', 'VACANT_REMAINING')",
                (guild_id, map_type, floor)
            ) as cursor:
                claims = [dict(r) for r in await cursor.fetchall()]

            events_map = {}
            async with db.execute(
                "SELECT event_name, last_triggered_at FROM floor_events WHERE guild_id = ? AND map_type = ? AND floor = ?",
                (guild_id, map_type, floor)
            ) as cursor:
                for r in await cursor.fetchall():
                    events_map[r["event_name"]] = r["last_triggered_at"]

        cog = self.bot.get_cog("ClaimCog")
        ticker = ""
        if cog:
            ticker = cog.calculate_ticker_line(map_type, floor)

        embed = MIR4Embeds.build_floor_embed(map_type, floor, claims, events_map, ticker)
        view = FloorEventButtonsView(self.bot, map_type, floor)

        if row:
            chan_id = row["channel_id"]
            channel = self.bot.get_channel(chan_id)
            if not channel:
                try:
                    channel = await self.bot.fetch_channel(chan_id)
                except:
                    channel = None
            if channel:
                try:
                    msg = await channel.fetch_message(row["message_id"])
                    await msg.edit(embed=embed, view=view)
                    return
                except discord.NotFound:
                    pass

        dest_channel = target_channel
        if dest_channel:
            new_msg = await dest_channel.send(embed=embed, view=view)
            async with DatabaseManager.get_connection() as db:
                await db.execute("""
                    INSERT INTO floor_dashboards (guild_id, map_type, floor, channel_id, message_id)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(guild_id, map_type, floor) DO UPDATE SET
                        channel_id = excluded.channel_id,
                        message_id = excluded.message_id
                """, (guild_id, map_type, floor, dest_channel.id, new_msg.id))
                await db.commit()
