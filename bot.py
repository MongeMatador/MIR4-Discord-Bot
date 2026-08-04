import discord
from discord.ext import commands
from aiohttp import web
from config import Config
from ui.main_panel import MainControlPanel

class HealthCheckServer:
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.runner = None
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/health', self.handle_health)

    async def handle_index(self, request):
        return web.Response(text="Bot Active", status=200)

    async def handle_health(self, request):
        return web.json_response({"status": "ok", "latency": round(self.bot.latency * 1000, 2)}, status=200)

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', Config.PORT)
        await site.start()

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

class MarsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=Config.CLIENT_ID if Config.CLIENT_ID != 0 else None
        )
        self.health_server = HealthCheckServer(self)

    async def setup_hook(self):
        await self.health_server.start()
        
        # REGISTRA A VIEW PERSISTENTE AO INICIAR
        self.add_view(MainControlPanel())

        await self.load_extension("cogs.admin_cog")
        await self.load_extension("cogs.claim_cog")
        await self.tree.sync()

    async def close(self):
        await self.health_server.stop()
        await super().close()

def run():
    if not Config.DISCORD_TOKEN:
        return
    bot = MarsBot()
    bot.run(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    run()
