import random
from collections.abc import Callable, Coroutine
from typing import cast

from discord import ButtonStyle, Embed, Interaction, Member, SelectOption, User
from discord.ui import Button, Select, View, button, select

from bot.core.codenames.constants import CODENAMES_ROLE, EMPTY, Colors, dictionaries
from bot.core.codenames.messages import messages
from bot.core.codenames.util import send_alert, send_error
from bot.core.database import Database


class StartView(View):
    def __init__(
        self,
        start_callback: Callable[
            [Interaction, list[User | Member], list[User | Member], str], Coroutine
        ],
        caller_id: int,
    ) -> None:
        super().__init__()

        self.start_callback = start_callback
        self.caller_id = caller_id

        self.game_started = False
        self.setup_done = False

        self.no_team: list[User | Member] = []
        self.team_red: list[User | Member] = []
        self.team_blue: list[User | Member] = []

        self.dictionary: str = "std"

        # Update the select menu with the current dictionary
        for child in self.children:
            if isinstance(child, Select):
                child.placeholder = f"Current: {dictionaries[self.dictionary]}"
                break

    def remove_player(self, player: Member | User) -> None:
        if player in self.no_team:
            self.no_team.remove(player)
        elif player in self.team_red:
            self.team_red.remove(player)
        elif player in self.team_blue:
            self.team_blue.remove(player)

    async def update(self, interaction: Interaction, *, final: bool = False) -> None:
        if self.no_team or self.team_red or self.team_blue:
            players_embed = Embed(
                title=messages.commands.game.setup_over if final else messages.commands.game.setup,
                color=Colors.teal,
            )

            players_embed.add_field(
                name=messages.commands.game.team_red,
                value="\n".join(map(lambda p: p.mention, self.team_red)) or EMPTY,
            )

            if not final:
                players_embed.add_field(
                    name=messages.commands.game.random,
                    value="\n".join(map(lambda p: p.mention, self.no_team)) or EMPTY,
                )

            players_embed.add_field(
                name=messages.commands.game.team_blue,
                value="\n".join(map(lambda p: p.mention, self.team_blue)) or EMPTY,
            )

        else:
            players_embed = Embed(
                title=messages.commands.game.setup,
                description=messages.commands.game.empty_list,
                color=Colors.teal,
            )

        if not final:
            players_embed.add_field(
                name=EMPTY,
                value=f"-# {messages.commands.game.setup_instructions}",
                inline=False,
            )
        players_embed.add_field(
            name="Dictionary", value=dictionaries[self.dictionary], inline=False
        )

        # Update the select menu with the current dictionary
        for child in self.children:
            if isinstance(child, Select):
                child.placeholder = f"Current: {dictionaries[self.dictionary]}"
                break
        await interaction.followup.edit_message(
            interaction.message.id,  # type: ignore
            embed=players_embed,
            view=None if final else self,
        )

    @button(emoji="🟥", style=ButtonStyle.grey, row=1)
    async def team_red_button(self, interaction: Interaction, _: Button) -> None:
        self.remove_player(interaction.user)

        self.team_red.append(interaction.user)

        await interaction.response.defer()
        await self.update(interaction)

    @button(emoji="❔", style=ButtonStyle.grey, row=1)
    async def no_team_button(self, interaction: Interaction, _: Button) -> None:
        self.remove_player(interaction.user)

        self.no_team.append(interaction.user)

        await interaction.response.defer()
        await self.update(interaction)

    @button(emoji="🟦", style=ButtonStyle.grey, row=1)
    async def team_blue_button(self, interaction: Interaction, _: Button) -> None:
        self.remove_player(interaction.user)

        self.team_blue.append(interaction.user)

        await interaction.response.defer()
        await self.update(interaction)

    @button(label=messages.ui.leave, emoji="❌", style=ButtonStyle.grey, row=2)
    async def leave_button(self, interaction: Interaction, _: Button) -> None:
        self.remove_player(interaction.user)

        await interaction.response.defer()
        await self.update(interaction)

    @button(label=messages.ui.cancel_reg, emoji="⛔", style=ButtonStyle.red, row=2)
    async def cancel_button(self, interaction: Interaction, _: Button) -> None:
        if (
            not interaction.user.id == self.caller_id
            and cast(Member, interaction.user).get_role(CODENAMES_ROLE) is None
        ):
            await interaction.response.defer()
            await send_error(interaction, messages.errors.title, messages.errors.not_host)
            return

        await send_alert(
            interaction,
            messages.ui.cancel_reg,
            self.cancel_callback,
            interaction,
        )

    @button(label=messages.ui.start_game, emoji="▶️", style=ButtonStyle.green, row=2)
    async def start_button(self, interaction: Interaction, _: Button) -> None:
        if cast(Member, interaction.user).get_role(CODENAMES_ROLE) is None:
            await interaction.response.defer()
            await send_error(interaction, messages.errors.title, messages.errors.not_host)
            return

        await send_alert(
            interaction,
            messages.ui.start_game,
            self.start_pre_callback,
            interaction,
        )

    @select(
        placeholder="Select a words dictionary...",
        min_values=1,
        max_values=1,
        options=[SelectOption(label=label, value=value) for value, label in dictionaries.items()],
    )
    async def select_dict(self, interaction: Interaction, select: Select) -> None:
        if cast(Member, interaction.user).get_role(CODENAMES_ROLE) is None:
            await interaction.response.defer()
            await send_error(interaction, messages.errors.title, messages.errors.not_host)
            return
        self.dictionary = select.values[0]
        await interaction.response.defer()
        await self.update(interaction)

    async def start_pre_callback(self, interaction: Interaction) -> None:
        if self.game_started:  # ignoring duplicate starts from same registration
            return

        no_team_temp = self.no_team.copy()
        team1_temp = self.team_red.copy()
        team2_temp = self.team_blue.copy()

        random.shuffle(no_team_temp)
        for member in no_team_temp:  # Dividing no_team into two teams randomly
            if len(team1_temp) <= len(team2_temp):
                team1_temp.append(member)
            else:
                team2_temp.append(member)

        if len(team1_temp) < 2 or len(team2_temp) < 2:
            await send_error(interaction, messages.errors.title, messages.errors.not_enough_players)
            return

        if len(team1_temp) > 25 or len(team2_temp) > 25:
            await send_error(interaction, messages.errors.title, messages.errors.too_many_players)
            return

        self.no_team = []
        self.team_red = team1_temp
        self.team_blue = team2_temp

        # Adding players to the database
        db = Database()
        all_players_ids = tuple(map(lambda p: p.id, self.team_red + self.team_blue))
        registered_ids = tuple(
            map(
                lambda row: row[0],
                await db.fetch(
                    f"SELECT id FROM players WHERE id IN ({', '.join(map(str, all_players_ids))})",
                    fetchall=True,
                ),  # type: ignore
            )
        )

        for _id in all_players_ids:
            if _id not in registered_ids:
                await db.exec_and_commit(
                    "INSERT INTO players VALUES (?, strftime('%d/%m/%Y','now'), ?, ?, ?, ?)",
                    (_id, 0, 0, 0, 0),
                )

        self.game_started = True

        await self.update(interaction, final=True)

        await self.start_callback(interaction, self.team_red, self.team_blue, self.dictionary)

    async def cancel_callback(self, interaction: Interaction) -> None:
        await interaction.followup.edit_message(
            interaction.message.id,  # type: ignore
            content=messages.commands.game.setup_cancelled,
            view=None,
        )
