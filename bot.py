import discord
from discord.ext import commands
from aiohttp import web
from config import config, logger
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
        return web.Response(text="MARS Discord Bot Active.", status=200)

    async def handle_health(self, request):
        is_ready = self.bot.is_ready()
        status_code = 200 if is_ready else 503
        data = {
            "status": "online" if is_ready else "starting",
            "latency_ms": round(self.bot.latency * 1000, 2) if is_ready else -1,
            "guilds": len(self.bot.guilds) if is_ready else 0
        }
        return web.json_response(data, status=status_code)

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', config.PORT)
        await site.start()
        logger.info(f"Health Check HTTP Server running on port {config.PORT}.")

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
            application_id=config.CLIENT_ID if config.CLIENT_ID != 0 else None
        )
        self.health_server = HealthCheckServer(self)

    async def setup_hook(self):
        # Inicia o servidor HTTP para o Render/UptimeRobot
        await self.health_server.start()

        # RE-REGISTRO GLOBAL DE PERSISTÊNCIA: Garante que o botão funcione após reboots do Render
        logger.info("Registrando View Persistente do Painel...")
        self.add_view(MainControlPanel())

        # Carrega as Cogs
        logger.info("Carregando cogs...")
        await self.load_extension("cogs.admin_cog")
        await self.load_extension("cogs.claim_cog")

        synced = await self.tree.sync()
        logger.info(f"Comandos Slash sincronizados: {len(synced)}")

    async def close(self):
        await self.health_server.stop()
        await super().close()

    async def on_ready(self):
        logger.info(f"Bot Online como {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="MIR4 Portals | /setup_panel")
        )

def run():
    if not config.DISCORD_TOKEN:
        logger.critical("DISCORD_TOKEN ausente nas variáveis de ambiente.")
        return

    bot = MarsBot()
    bot.run(config.DISCORD_TOKEN)

if __name__ == "__main__":
    run()
