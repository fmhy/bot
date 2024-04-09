import traceback
from datetime import datetime, timedelta, timezone

import discord
import humanize
from discord import (
    Interaction,
    app_commands as app,
)
from discord.ext import commands

from bot.core import Bot


class Errors(commands.Cog):
    """Error handler for commands and interactions."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.bot.on_command_error = self.on_command_error
        self.bot.tree.on_error = self.on_tree_error

    async def on_tree_error(self, interaction: Interaction[Bot], error: app.AppCommandError):
        if isinstance(error, app.CommandNotFound):
            await interaction.response.send_message(
                f"Could not find {error.name}, it was probably updated or removed.", ephemeral=True
            )
        if isinstance(error, app.CommandOnCooldown):
            relative_time = discord.utils.format_dt(
                datetime.now(timezone.utc) + timedelta(seconds=error.retry_after), "R"
            )
            await interaction.response.send_message(
                f"This command is on cooldown, try again {relative_time}.",
                ephemeral=True,
            )
        else:
            self.bot.logger.error(
                f"{type(error).__name__}: {error} ({interaction.command.name})",  # type: ignore
                exc_info=error,
            )
            traceback.print_exc()

    async def on_command_error(self, ctx: commands.Context, e: Exception):
        e = getattr(e, "original", e)
        if isinstance(e, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(e, commands.DisabledCommand):
            await ctx.author.send("Sorry. This command is disabled and cannot be used.")
        ignored = (
            commands.CommandNotFound,
            commands.CheckFailure,
            commands.BadArgument,
        )
        if isinstance(e, commands.MissingPermissions):
            await ctx.send(
                "You do not have the following permissions: `{}`".format(
                    ", ".join(e.missing_permissions)
                )
            )
        elif isinstance(e, ignored):
            pass
        elif isinstance(e, commands.BotMissingPermissions):
            await ctx.send("I'm missing: `{}`".format(", ".join(e.missing_permissions)))
        elif isinstance(e, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument: `{e.param}`")
        elif isinstance(e, commands.CommandOnCooldown):
            await ctx.send(
                f"This command is on cooldown, try again in {humanize.naturaldelta(e.retry_after)}"
            )
        elif isinstance(e, commands.TooManyArguments):
            await ctx.send(str(e))
        else:
            self.bot.logger.error(f"{type(e).__name__}: {e} ({ctx.command.name})")  # type: ignore
            traceback.print_exc()


async def setup(bot: Bot):
    await bot.add_cog(Errors(bot))
