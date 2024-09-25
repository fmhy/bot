from collections.abc import Callable
from typing import TypeVar

from discord import Interaction, User
from discord.app_commands import NoPrivateMessage, check
from discord.app_commands.errors import CheckFailure

from bot.core.codenames.constants import CODENAMES_CHANNEL, CODENAMES_ROLE

T = TypeVar("T")


class CodenamesHostError(CheckFailure):
    def __init__(self) -> None:
        super().__init__("You are not a codenames host.")


class CodenamesChannelError(CheckFailure):
    def __init__(self) -> None:
        super().__init__("This command can only be used in the codenames channel.")


def is_codenames() -> Callable[[T], T]:
    async def predicate(interaction: Interaction) -> bool:
        if isinstance(interaction.user, User):
            raise NoPrivateMessage()

        role = interaction.user.get_role(CODENAMES_ROLE)

        if role is None:
            raise CodenamesHostError()

        if (
            interaction.guild
            and interaction.channel
            and interaction.channel.id != CODENAMES_CHANNEL
        ):
            raise CodenamesChannelError()

        return True

    return check(predicate)
