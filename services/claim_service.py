import discord
import aiosqlite
from datetime import datetime, timedelta
from config import Config

class DatabaseManager:
    @staticmethod
    async def initialize():
        async with aiosqlite.connect(Config.DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS floor_dashboards (
                    map_type TEXT NOT NULL,
                    floor TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER,
                    PRIMARY KEY (map_type, floor)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    map_type TEXT NOT NULL,
                    floor TEXT NOT NULL,
                    spot_type TEXT NOT NULL,
                    room_number INTEGER NOT NULL DEFAULT 1,
                    tickets INTEGER NOT NULL,
                    started_at DATETIME NOT NULL,
                    ends_at DATETIME NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE'
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS spot_queues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    map_type TEXT NOT NULL,
                    floor TEXT NOT NULL,
                    spot_type TEXT NOT NULL,
                    tickets INTEGER NOT NULL,
                    queued_at DATETIME NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS floor_events (
                    map_type TEXT NOT NULL,
                    floor TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    last_triggered_at TEXT,
                    PRIMARY KEY (map_type, floor, event_name)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS admin_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_claims_perf ON claims (map_type, floor, spot_type, status);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_queues_perf ON spot_queues (map_type, floor, spot_type, queued_at);")
            await db.commit()
            await DatabaseManager._seed_events()

    @staticmethod
    async def _seed_events():
        async with aiosqlite.connect(Config.DB_PATH) as db:
            for map_key, map_info in Config.MAP_DATA.items():
                for floor in map_info["floors"].keys():
                    for event in Config.TRACKABLE_EVENTS[map_key].keys():
                        await db.execute(
                            "INSERT OR IGNORE INTO floor_events (map_type, floor, event_name, last_triggered_at) VALUES (?, ?, ?, NULL)",
                            (map_key, floor, event)
                        )
            await db.commit()

    @staticmethod
    def get_connection():
        return aiosqlite.connect(Config.DB_PATH)


class ClaimService:
    @staticmethod
    async def check_user_status(user_id: int, map_type: str) -> tuple:
        """Garante suporte a multi-contas simultâneas separadas por mapa"""
        async with DatabaseManager.get_connection() as db:
            async with db.execute("""
                SELECT 
                    (SELECT 1 FROM claims WHERE user_id = ? AND map_type = ? AND status = 'ACTIVE' LIMIT 1) as has_claim,
                    (SELECT 1 FROM spot_queues WHERE user_id = ? AND map_type = ? LIMIT 1) as in_queue
            """, (user_id, map_type, user_id, map_type)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return bool(row[0]), bool(row[1])
                return False, False

    @staticmethod
    async def get_boss_owner(map_type: str, floor: str) -> int:
        """SEGURANÇA: Retorna a ID do dono do Boss para travar os botões de minério/selar"""
        async with DatabaseManager.get_connection() as db:
            async with db.execute(
                "SELECT user_id FROM claims WHERE map_type = ? AND floor = ? AND spot_type = 'BOSS' AND status = 'ACTIVE' LIMIT 1",
                (map_type, floor)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    @staticmethod
    async def prepare_spot_interaction(map_type: str, floor: str, spot_type: str, max_rooms: int) -> tuple:
        """BATCH QUERY: Consolida rotinas para eliminar o lag de cliques do assistente"""
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute(
                "SELECT COUNT(id) FROM spot_queues WHERE map_type = ? AND floor = ? AND spot_type = ?",
                (map_type, floor, spot_type)
            ) as cursor:
                q_row = await cursor.fetchone()
                queue_count = q_row[0] if q_row else 0
                
            if queue_count == 0:
                await db.execute(
                    "UPDATE claims SET status = 'CANCELLED' WHERE map_type = ? AND floor = ? AND spot_type = ? AND status = 'VACANT_REMAINING'",
                    (map_type, floor, spot_type)
                )
                await db.commit()
                
            async with db.execute(
                "SELECT * FROM claims WHERE map_type = ? AND floor = ? AND spot_type = ? AND status = 'VACANT_REMAINING' ORDER BY ends_at ASC LIMIT 1",
                (map_type, floor, spot_type)
            ) as cursor:
                vacant_room = await cursor.fetchone()
                vacant_room_dict = dict(vacant_room) if vacant_room else None
                
            async with db.execute(
                "SELECT room_number FROM claims WHERE map_type = ? AND floor = ? AND spot_type = ? AND status IN ('ACTIVE', 'VACANT_REMAINING')",
                (map_type, floor, spot_type)
            ) as cursor:
                rows = await cursor.fetchall()
                occupied_rooms = [r['room_number'] for r in rows]
                
            empty_room = None
            for room in range(1, max_rooms + 1):
                if room not in occupied_rooms:
                    empty_room = room
                    break
                    
            return vacant_room_dict, empty_room, queue_count

    @staticmethod
    async def get_active_claims_for_spot(map_type: str, floor: str, spot_type: str) -> list:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM claims WHERE map_type = ? AND floor = ? AND spot_type = ? AND status IN ('ACTIVE', 'VACANT_REMAINING')",
                (map_type, floor, spot_type)
            ) as cursor:
                return await cursor.fetchall()

    @staticmethod
    async def find_vacant_remaining_room(map_type: str, floor: str, spot_type: str) -> dict:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM claims WHERE map_type = ? AND floor = ? AND spot_type = ? AND status = 'VACANT_REMAINING' ORDER BY ends_at ASC LIMIT 1",
                (map_type, floor, spot_type)
            ) as cursor:
                return await cursor.fetchone()

    @staticmethod
    async def claim_vacant_remaining(claim_id: int, user_id: int, username: str):
        async with DatabaseManager.get_connection() as db:
            await db.execute(
                "UPDATE claims SET user_id = ?, username = ?, status = 'ACTIVE' WHERE id = ?",
                (user_id, username, claim_id)
            )
            await db.commit()

    @staticmethod
    async def find_first_empty_room(map_type: str, floor: str, spot_type: str, max_rooms: int) -> int:
        claims = await ClaimService.get_active_claims_for_spot(map_type, floor, spot_type)
        occupied_rooms = [c['room_number'] for c in claims]
        for room in range(1, max_rooms + 1):
            if room not in occupied_rooms:
                return room
        return None

    @staticmethod
    async def create_claim(user_id: int, username: str, map_type: str, floor: str, spot_type: str, room_number: int, tickets: int) -> datetime:
        duration_minutes = tickets * 30
        started_at = datetime.utcnow()
        ends_at = started_at + timedelta(minutes=duration_minutes)
        async with DatabaseManager.get_connection() as db:
            await db.execute(
                """INSERT INTO claims (user_id, username, map_type, floor, spot_type, room_number, tickets, started_at, ends_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')""",
                (user_id, username, map_type, floor, spot_type, room_number, tickets, started_at.isoformat(), ends_at.isoformat())
            )
            await db.commit()
        return ends_at

    @staticmethod
    async def cancel_active_claim(user_id: int, map_type: str) -> tuple:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM claims WHERE user_id = ? AND map_type = ? AND status = 'ACTIVE'", (user_id, map_type)
            ) as cursor:
                claim = await cursor.fetchone()
            
            if claim:
                queue_count = await ClaimService.get_queue_count(claim['map_type'], claim['floor'], claim['spot_type'])
                if queue_count > 0:
                    await db.execute(
                        "UPDATE claims SET user_id = 0, username = 'Tempo Restante', status = 'VACANT_REMAINING' WHERE id = ?",
                        (claim['id'],)
                    )
                    await db.commit()
                    return True, claim['map_type'], claim['floor'], claim['spot_type'], claim['room_number'], True
                else:
                    await db.execute("UPDATE claims SET status = 'CANCELLED' WHERE id = ?", (claim['id'],))
                    await db.commit()
                    return True, claim['map_type'], claim['floor'], claim['spot_type'], claim['room_number'], False
            return False, None, None, None, None, False

    @staticmethod
    async def get_queue_count(map_type: str, floor: str, spot_type: str) -> int:
        async with DatabaseManager.get_connection() as db:
            async with db.execute(
                "SELECT COUNT(id) FROM spot_queues WHERE map_type = ? AND floor = ? AND spot_type = ?", (map_type, floor, spot_type)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    @staticmethod
    async def add_to_queue(user_id: int, username: str, map_type: str, floor: str, spot_type: str, tickets: int) -> bool:
        current_count = await ClaimService.get_queue_count(map_type, floor, spot_type)
        if current_count >= Config.MAX_QUEUE_SIZE:
            return False
            
        async with DatabaseManager.get_connection() as db:
            await db.execute(
                """INSERT INTO spot_queues (user_id, username, map_type, floor, spot_type, tickets, queued_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, username, map_type, floor, spot_type, tickets, datetime.utcnow().isoformat())
            )
            await db.commit()
        return True

    # RESTAURADO: Coleta o próximo guerreiro da lista de espera
    @staticmethod
    async def get_next_in_queue(map_type: str, floor: str, spot_type: str) -> dict:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM spot_queues WHERE map_type = ? AND floor = ? AND spot_type = ? ORDER BY queued_at ASC LIMIT 1",
                (map_type, floor, spot_type)
            ) as cursor:
                return await cursor.fetchone()

    # RESTAURADO: Deleta o integrante da lista após herdar a sala
    @staticmethod
    async def remove_from_queue(queue_id: int):
        async with DatabaseManager.get_connection() as db:
            await db.execute("DELETE FROM spot_queues WHERE id = ?", (queue_id,))
            await db.commit()

    # RESTAURADO: Fornece a listagem nominal para o placar público
    @staticmethod
    async def get_queue_list(map_type: str, floor: str, spot_type: str) -> list:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM spot_queues WHERE map_type = ? AND floor = ? AND spot_type = ? ORDER BY queued_at ASC",
                (map_type, floor, spot_type)
            ) as cursor:
                return await cursor.fetchall()

    # RESTAURADO: Puxa os dados dos cronômetros do painel
    @staticmethod
    async def get_floor_events(map_type: str, floor: str) -> list:
        async with DatabaseManager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM floor_events WHERE map_type = ? AND floor = ?", (map_type, floor)) as cursor:
                return await cursor.fetchall()

    @staticmethod
    async def update_event_time(map_type: str, floor: str, event_name: str, timestamp_iso: str):
        async with DatabaseManager.get_connection() as db:
            await db.execute(
                "UPDATE floor_events SET last_triggered_at = ? WHERE map_type = ? AND floor = ? AND event_name = ?",
                (timestamp_iso, map_type, floor, event_name)
            )
            await db.commit()

    @staticmethod
    async def dispatch_admin_log(bot: discord.Client, action_type: str, user: discord.User, map_type: str, floor: str, spot_type: str, room: int, duration_mins: int = 0):
        setting_key = f"log_channel_id_{map_type}"
        async with DatabaseManager.get_connection() as db:
            async with db.execute("SELECT setting_value FROM admin_settings WHERE setting_key = ?", (setting_key,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return
                channel_id = int(row[0])
                
        channel = bot.get_channel(channel_id)
        if not channel:
            return

        map_name = Config.MAP_DATA[map_type]["label"]
        colors = {"CLAIM": 0x2ecc71, "CANCEL": 0xe74c3c, "EXPIRED": 0x95a5a6, "QUEUE": 0xe67e22, "HERANÇA": 0x3498db}
        emojis = {"CLAIM": "📥", "CANCEL": "📤", "EXPIRED": "⏰", "QUEUE": "⏳", "HERANÇA": "♻️"}
        
        server_log_time = datetime.utcnow() + timedelta(hours=Config.TIMEZONE_OFFSET)
        
        embed = discord.Embed(
            title=f"{emojis.get(action_type, '📝')} Auditoria Executiva | {action_type}",
            color=colors.get(action_type, 0x1a1a1a)
        )
        embed.add_field(name="Guerreiro", value=f"{user.mention} (`{user.name}`)", inline=True)
        embed.add_field(name="Ecossistema", value=map_name, inline=True)
        embed.add_field(name="Alocação", value=f"Andar: **{floor}** | Spot: **{spot_type}**", inline=True)
        
        if room > 0 and map_type == "MAGIC_SQUARE":
            embed.add_field(name="Sub-Sala", value=f"Sala {room}", inline=True)
        if duration_mins > 0:
            embed.add_field(name="Janela de Farm", value=f"`{duration_mins} minutos`", inline=True)
            
        embed.add_field(name="⏰ Horário do Registro (Servidor)", value=f"`{server_log_time.strftime('%H:%M:%S')}`", inline=False)
            
        try:
            await channel.send(embed=embed)
        except:
            pass