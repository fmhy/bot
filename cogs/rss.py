from typing import TYPE_CHECKING

from discord.ext import commands, tasks

from cogs._config import rss_chan_ids
from cogs._helpers import fetch_feed
from main import Bot

if TYPE_CHECKING:
    from discord.channel import TextChannel


class RSSFeeds(commands.Cog):
    """RSSFeeds commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.send_rss.start()

    async def cog_before_invoke(self, ctx):
        """Triggers typing indicator on Discord before every command."""
        await ctx.channel.typing()
        return

    @tasks.loop(seconds=300)
    async def send_rss(self):
        for msg in fetch_feed():
            for channel_id in rss_chan_ids:
                # FIXME: pyright complains, typecast this to TextChannel somehow
                chan: TextChannel = await self.bot.fetch_channel(channel_id)
                await chan.send(msg)


async def setup(bot: Bot):
    await bot.add_cog(RSSFeeds(bot))
