from discord.channel import TextChannel
from discord.ext import commands, tasks

from bot.core import Bot
from bot.core.config import rss_chan_ids
from bot.core.helpers import fetch_feed


class RSSFeeds(commands.Cog):
    """RSS relating commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self):
        self.send_rss.start()

    async def cog_unload(self) -> None:
        self.send_rss.stop()
        return await super().cog_unload()

    @tasks.loop(seconds=300)
    async def send_rss(self):
        for msg in fetch_feed():
            for channel_id in rss_chan_ids:
                chan = self.bot.get_partial_messageable(channel_id, guild_id=None)
                if not isinstance(chan, TextChannel):
                    continue
                await chan.send(msg)


async def setup(bot: Bot):
    await bot.add_cog(RSSFeeds(bot))
