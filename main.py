# Alias para garantir compatibilidade se o Render iniciar por main.py
from bot import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
