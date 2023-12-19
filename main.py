import datetime
from discord.ext import commands
import discord
from cogs._config import token, prefix, owners
import os
import aiohttp
import time
import traceback
import logging
import sys
from core import formatter

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"


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
        formatter.install("discord", "INFO")
        formatter.install("bot", "INFO")
        self.logger = logging.getLogger("discord")
        self.logger = logging.getLogger("bot")

    async def setup_hook(self):
        await self.load_extension("jishaku")
        await self.load_cogs()

    async def load_cogs(self):
        s = time.perf_counter()
        for file in os.listdir("cogs/"):
            if file.endswith(".py") and not file.startswith("_"):
                extension = f"cogs.{file[:-3]}"
                try:
                    await self.load_extension(extension)
                    self.logger.info(f"Loaded - {extension}")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.exception(f"Failed to load extension {extension}. - {exception}")
                    traceback.print_exc()

        elapsed = time.perf_counter() - s
        self.logger.info(f"Loaded all extensions - took {elapsed:.2f}s")

    async def is_owner(self, user: discord.abc.User):
        if user.id in owners:
            return True
        # Else fall back to the original
        return await super().is_owner(user)

    async def on_ready(self) -> None:
        self.session = aiohttp.ClientSession(loop=self.loop)
        await self.change_presence(activity=discord.Game(name="Free Media Heck Yeah"))
        print("Bot is ready!")


if __name__ == "__main__":
    bot = FMBY()
    try:
        bot.run(token, log_handler=None)
    except Exception as e:
        bot.logger.error(f"{type(e).__name__}: {e}")
        traceback.print_exc()
    except KeyboardInterrupt:
        bot.logger.info("Shutting down...")
        bot.loop.run_until_complete(bot.session.close())
        bot.logger.info("Goodbye!")
    finally:
        sys.exit()
