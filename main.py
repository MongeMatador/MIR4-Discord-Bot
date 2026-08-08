import asyncio
import discord
from aiohttp import web
from discord.ext import commands
from config import DISCORD_TOKEN, PORT
from database.connection import DatabaseConnection
from database.repositories.panel_repository import PanelRepository
from database.repositories.claim_repository import ClaimRepository
from database.repositories.log_repository import LogRepository
from services.panel_service import PanelService
from services.log_service import LogService
from services.claim_service import ClaimService
from ui.views import MIR4PanelPersistentView
from utils.logger import log

class MIR4Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents)

        # Repositórios
        self.panel_repo = PanelRepository()
        self.claim_repo = ClaimRepository()
        self.log_repo = LogRepository()

        # Serviços
        self.panel_service = PanelService(self, self.panel_repo, self.claim_repo)
        self.log_service = LogService(self, self.log_repo)
        self.claim_service = ClaimService(self.claim_repo, self.panel_service, self.log_service)

    async def setup_hook(self):
        log.info("Inicializando infraestrutura de banco de dados...")
        await DatabaseConnection.init_db()

        # View Persistente para o Painel Único
        self.add_view(MIR4PanelPersistentView(self))

        log.info("Carregando módulos Cogs...")
        await self.load_extension("cogs.claim_cog")
        await self.load_extension("cogs.admin_cog")
        await self.load_extension("cogs.logs_cog")

        log.info("Sincronizando comandos Slash com o Discord...")
        await self.tree.sync()

    async def on_ready(self):
        log.info(f"🤖 Bot autenticado como {self.user} (ID: {self.user.id})")

# Servidor Web Leve para o UptimeRobot Manter o Render Online
async def handle_ping(request):
    return web.Response(text="MIR4 Discord Bot - Online 24/7", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info(f"🌐 Servidor Web de HealthCheck (UptimeRobot) ativo na porta {PORT}")

async def main():
    bot = MIR4Bot()
    await start_web_server()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
