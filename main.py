import datetime
from discord.ext import commands
import discord
from cogs._config import token, prefix, owners
import os
import aiohttp


class HelpMenu(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(description=page, color=discord.Color.teal())
            embed.set_footer(
                text="Use help [command] or help [category] | <> is required | [] is optional"
            )
            embed.timestamp = datetime.datetime.now(datetime.UTC)
            await destination.send(embed=embed)


class FMBY(commands.Bot):
    def __init__(self) -> None:
        self.start_time = datetime.datetime.now(datetime.UTC)
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=commands.when_mentioned_or(prefix),
            intents=intents,
            help_command=HelpMenu(),
            case_insensitive=True,
        )

        self.session: aiohttp.ClientSession

    async def setup_hook(self):
        await self.load_extension("jishaku")
        # await self.load_cogs()

    async def load_cogs(self):
        for file in os.listdir("cogs/"):
            if file.endswith(".py") and not file.startswith("_"):
                await bot.load_extension(f"cogs.{file[:-3]}")

    async def is_owner(self, user: discord.abc.User):
        if user.id in owners:
            return True
        # Else fall back to the original
        return await super().is_owner(user)

    async def on_ready(self) -> None:
        self.session = aiohttp.ClientSession(loop=self.loop)
        await self.change_presence(activity=discord.Game(name="Free Media Heck Yeah"))
        print("Bot is ready!")


bot = FMBY()


@bot.event
async def on_command_error(ctx: commands.Context, error):
    if hasattr(ctx.command, "on_error"):
        return
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        return


@bot.command(description="Shows the bot's latency")
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms • started {bot.start_time}")


if __name__ == "__main__":
    # When running this file, if it is the 'main' file
    # i.e. its not being imported from another python file run this
    bot.run(token)
