import traceback

import humanize
from discord.ext import commands

from discord.app_commands import errors
from main import Bot


class Errors(commands.Cog):
    """Error handler for commands."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def on_command_error(self, ctx: commands.Context, e: Exception):
        e = getattr(e, "olriginal", e)
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
        elif isinstance(e, errors.CommandOnCooldown):
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
