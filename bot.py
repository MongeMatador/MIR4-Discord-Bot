import asyncio
import discord
from aiohttp import web
from discord.ext import commands
from config import Config, logger
from database.connection import DatabaseConnection
from database.repositories.panel_repository import PanelRepository
from database.repositories.claim_repository import ClaimRepository
from database.repositories.log_repository import LogRepository
from services.panel_service import PanelService
from services.log_service import LogService
from services.claim_service import ClaimService
from ui.views import MIR4MSPanelPersistentView, MIR4PSPanelPersistentView

class MIR4Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

        # Injeção de Repositórios
        self.panel_repo = PanelRepository()
        self.claim_repo = ClaimRepository()
        self.log_repo = LogRepository()

        # Injeção de Serviços
        self.panel_service = PanelService(self, self.panel_repo, self.claim_repo)
        self.log_service = LogService(self, self.log_repo)
        self.claim_service = ClaimService(self.claim_repo, self.panel_service, self.log_service)

    async def setup_hook(self):
        logger.info("Inicializando infraestrutura de Banco de Dados...")
        await DatabaseConnection.init_db()

        # Registra as duas Views Persistentes de cada mapa para suporte contínuo no Render
        self.add_view(MIR4MSPanelPersistentView(self))
        self.add_view(MIR4PSPanelPersistentView(self))

        logger.info("Carregando módulos Cogs...")
        await self.load_extension("cogs.claim_cog")
        await self.load_extension("cogs.admin_cog")
        await self.load_extension("cogs.logs_cog")

        logger.info("Sincronizando comandos Slash com a API do Discord...")
        await self.tree.sync()

    async def on_ready(self):
        logger.info(f"🤖 Bot autenticado com sucesso como: {self.user} (ID: {self.user.id})\")")

async def handle_ping(request):
    return web.Response(text="MIR4 Discord Bot - Online 24/7", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", Config.PORT)
    await site.start()
    logger.info(f"🌐 Servidor Web de HealthCheck (UptimeRobot) ativo na porta {Config.PORT}")

async def main():
    Config.validate()
    bot = MIR4Bot()
    await start_web_server()
    async with bot:
        await bot.start(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot encerrado manualmente.")
    except Exception as e:
        logger.critical(f"Erro fatal na inicialização: {e}", exc_info=True)
