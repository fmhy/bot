from aiohttp import ClientSession

from bot.core import Bot
from bot.core.config import TOKEN


async def main():
    async with ClientSession() as session:
        async with Bot(session=session) as bot:
            await bot.start(TOKEN)
