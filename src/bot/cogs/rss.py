from discord.channel import ForumChannel
from discord.ext import commands, tasks

from bot.core import Bot
from bot.core.config import news_forum, news_tag
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
            forum = self.bot.get_channel(news_forum)
            if not isinstance(forum, ForumChannel):
                return
            tag = forum.get_tag(news_tag)
            if not tag:
                return
            await forum.create_thread(
                name=feed.title,
                content=feed.link,
                reason="Thread created by FMHY Bot",
                applied_tags=[tag],
            )


async def setup(bot: Bot):
    await bot.add_cog(RSSFeeds(bot))
