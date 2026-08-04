import discord
from discord.ext import commands
from aiohttp import web
from config import Config, logger
from services.claim_service import claim_service
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
        return web.Response(text="MARS Discord Bot Engine Active.", status=200)

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
        site = web.TCPSite(self.runner, '0.0.0.0', Config.PORT)
        await site.start()
        logger.info(f"Health Check HTTP Server rodando na porta {Config.PORT} para Render e UptimeRobot.")

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
        # 1. Inicia o Servidor HTTP para Render e UptimeRobot
        await self.health_server.start()

        # 2. REGISTRA A VIEW PERSISTENTE NO BOOT (CORRIGE O BOTÃO TRAVADO NO '...')
        logger.info("Registrando ouvinte da View Persistente (MainControlPanel)...")
        self.add_view(MainControlPanel())

        # 3. Carrega as Cogs do repositório
        logger.info("Carregando cogs...")
        await self.load_extension("cogs.admin_cog")
        await self.load_extension("cogs.claim_cog")

        # 4. Sincroniza Comandos Slash
        synced = await self.tree.sync()
        logger.info(f"Sucesso: {len(synced)} comandos Slash sincronizados.")

    async def close(self):
        await self.health_server.stop()
        await super().close()

    async def on_ready(self):
        logger.info(f"Bot Autenticado com Sucesso: {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="MIR4 Portals | /setup_panel")
        )

def run():
    if not Config.DISCORD_TOKEN:
        logger.critical("DISCORD_TOKEN ausente nas variáveis de ambiente!")
        return

    bot = MarsBot()
    bot.run(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    run()
