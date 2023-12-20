from discord.ext import commands

from main import FMBY


class General(commands.Cog):
    """General commands"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_before_invoke(self, ctx):
        """Triggers typing indicator on Discord before every command
        """
        await ctx.trigger_typing()
        return

    @commands.command()
    async def cmd(self, ctx):
        ...


def setup(bot: FMBY):
    bot.add_cog(General(bot))
