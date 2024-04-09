import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Coroutine, Optional, ParamSpec, Tuple, TypeVar

import aiohttp
import discord
from discord.ext import commands

from bot.core import formatter, help
from bot.core.config import OWNERS, prefix

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"

P = ParamSpec("P")
T = TypeVar("T")


def _wrap_extension(
    func: Callable[P, Awaitable[T]],
) -> Callable[P, Coroutine[Any, Any, Optional[T]]]:
    async def log_extension(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        fmt_args = 'on ext "{}"{}'.format(args[1], f" with kwargs {kwargs}" if kwargs else "")
        start = time.monotonic()

        try:
            logger = args[0].logger  # type: ignore
        except:
            logger = logging

        try:
            result = await func(*args, **kwargs)
        except Exception as exc:
            logger.error(
                f"Failed to load extension in {(time.monotonic() - start)*1000:.2f}ms {fmt_args}",
                exc_info=exc,
            )
            raise

        fmt = f"{func.__name__} took {(time.monotonic() - start)*1000:.2f}ms {fmt_args}"
        logger.info(fmt)

        return result

    return log_extension


initial_extensions: Tuple[str, ...] = (
    # Core
    "jishaku",
    "bot.cogs.errors",
    "bot.cogs.events",
    # Cogs
    "bot.cogs.fun",
    "bot.cogs.wiki",
    "bot.cogs.rss",
)


class Bot(commands.Bot):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.start_time = datetime.now(timezone.utc)
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=commands.when_mentioned_or(prefix),
            intents=intents,
            help_command=help.HelpMenu(),
            case_insensitive=True,
            owner_ids=OWNERS,
        )
        self.session: aiohttp.ClientSession = session
        formatter.install("discord", "INFO")
        formatter.install("bot", "INFO")
        self.logger = logging.getLogger("bot")

    async def setup_hook(self):
        for extension in initial_extensions:
            await self.load_extension(extension)
        self.logger.info(f"Loaded all {len(initial_extensions)} extensions.")

    async def on_ready(self) -> None:
        await self.tree.sync()
        await self.change_presence(activity=discord.Game(name="/r/freemediaheckyeah"))
        self.logger.info(f"Bot is ready as {self.user.display_name}!")  # type: ignore

    @_wrap_extension
    @discord.utils.copy_doc(commands.Bot.load_extension)
    async def load_extension(self, name: str, *, package: Optional[str] = None) -> None:
        try:
            await super().load_extension(name, package=package)
        except:
            raise

    @_wrap_extension
    @discord.utils.copy_doc(commands.Bot.unload_extension)
    async def unload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        try:
            await super().unload_extension(name, package=package)
        except:
            raise

    @_wrap_extension
    @discord.utils.copy_doc(commands.Bot.reload_extension)
    async def reload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        try:
            await super().reload_extension(name, package=package)
        except:
            raise
