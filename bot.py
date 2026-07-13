import discord
from discord.ext import commands
from config import Config
from services.claim_service import DatabaseManager
from ui.main_panel import MainControlPanel
from ui.floor_events_view import FloorEventButtonsView
from aiohttp import web
import asyncio

class Mir4ClaimBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await DatabaseManager.initialize()
        await self.load_extension("cogs.claim_cog")
        await self.load_extension("cogs.admin_cog")
        
        self.add_view(MainControlPanel("MAGIC_SQUARE"))
        self.add_view(MainControlPanel("SECRET_PEAK"))
        
        for map_key, map_info in Config.MAP_DATA.items():
            for floor in map_info["floors"].keys():
                self.add_view(FloorEventButtonsView(map_key, floor))

    async def on_ready(self):
        print(f"==========================================")
        print(f"🤖 Arquiteto de Sistemas MIR4 Online Ativo: {self.user.name}")
        print(f"🌍 Multi-Tenant Engine Operando em Fuso UTC-4")
        print(f"==========================================")

# Retorna uma mensagem de texto simples quando a hospedagem testar a porta
async def handle(request):
    return web.Response(text="Bot MIR4 Online 24/7")

async def main():
    bot = Mir4ClaimBot()
    
    # Inicializa o mini-servidor HTTP de forma assíncrona na porta da nuvem
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
    
    # Dispara o servidor web em background e inicia o bot do Discord
    asyncio.create_task(site.start())
    await bot.start(Config.TOKEN)

if __name__ == "__main__":
    asyncio.run(main())