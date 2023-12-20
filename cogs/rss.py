from discord.ext import commands, tasks

from cogs._config import rss_chan_ids
from cogs._helpers import fetch_feed


class RSSFeeds(commands.Cog):
    """RSSFeeds commands"""

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.send_rss.start()

    async def cog_before_invoke(self, ctx):
        """Triggers typing indicator on Discord before every command.
        """
        await ctx.trigger_typing()
        return

    @tasks.loop(seconds=300)
    async def send_rss(self):
        for msg in fetch_feed():
            for channel_id in rss_chan_ids:
                chan = await self.bot.fetch_channel(channel_id)
                await chan.send(msg)


def setup(bot):
    bot.add_cog(RSSFeeds(bot))
