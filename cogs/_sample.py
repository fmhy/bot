from discord.ext import commands

from main import Bot


class General(commands.Cog):
    """General commands"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_before_invoke(self, ctx):
        """Triggers typing indicator on Discord before every command"""
        await ctx.channel.typing()
        return

    @commands.command()
    async def cmd(self, ctx):
        ...


async def setup(bot: Bot):
    await bot.add_cog(General(bot))
