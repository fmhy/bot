from typing import TYPE_CHECKING

from discord.ext import commands, tasks

from bot.core import Bot
from bot.core.config import rss_chan_ids
from bot.core.helpers import fetch_feed

if TYPE_CHECKING:
    from discord.channel import TextChannel


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
                # FIXME: pyright complains, typecast this to TextChannel somehow
                chan: TextChannel = await self.bot.fetch_channel(channel_id)  # type: ignore
                await chan.send(msg)


async def setup(bot: Bot):
    await bot.add_cog(RSSFeeds(bot))
