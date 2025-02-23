from discord.channel import Thread
from discord.ext import commands, tasks

from bot.core import Bot
from bot.core.config import news_forum
from bot.core.helpers import fetch_feeds


class RSSFeeds(commands.Cog):
    """RSS related events cog."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self):
        self.send_rss.start()

    async def cog_unload(self) -> None:
        self.send_rss.stop()
        return await super().cog_unload()

    @tasks.loop(seconds=300)
    async def send_rss(self):
        for feed in fetch_feeds():
            thread = await self.bot.fetch_channel(news_forum)
            if not isinstance(thread, Thread):
                self.bot.logger.error("No news thread available")
                return
            await thread.send(content=f"{feed.title} | {feed.link}")


async def setup(bot: Bot):
    await bot.add_cog(RSSFeeds(bot))
