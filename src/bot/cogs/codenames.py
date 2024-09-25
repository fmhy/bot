import asyncio
import os
import random
import re
import shutil
from typing import Literal, cast
from uuid import uuid4 as get_uuid

from discord import Embed, File, Guild, Interaction, Member, PartialMessageable, Role, User
from discord.app_commands import Choice, choices, command, describe
from discord.ext.commands import GroupCog

import bot.core.codenames.generation as gen
from bot import Bot
from bot.core.checks import is_codenames
from bot.core.codenames.constants import (
    ALPHABET,
    CODENAMES_BLUE_SPYMASTER_ROLE,
    CODENAMES_BLUE_TEAM_ROLE,
    CODENAMES_RED_SPYMASTER_ROLE,
    CODENAMES_RED_TEAM_ROLE,
    EMPTY,
    GUIDE,
    REACTION_ALPHABET,
    REACTION_R,
    Colors,
    Paths,
)
from bot.core.codenames.messages import messages
from bot.core.codenames.ui import StartView
from bot.core.codenames.util import most_count_reaction_emojis, send_error, send_fields, vote


# thanks owoer
def mock_user(n: int, bot: Bot) -> User:
    obj = {
        "id": random.randint(10000000000000000, 1000000000000000000),
        "username": "MockUser" + str(n),
        "avatar": None,
        "discriminator": "0",
    }
    return User(state=bot._connection, data=obj)  # type: ignore  # noqa: SLF001


class Codenames(GroupCog, name="codenames"):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @command(name="start", description="Start a new game of codenames.")
    @is_codenames()
    async def start(self, interaction: Interaction[Bot]) -> None:
        start_view = StartView(self._start, interaction.user.id)

        # # Add mock users
        # mock_users = [
        #     mock_user(1, self.bot),
        #     mock_user(2, self.bot),
        #     mock_user(3, self.bot),
        # ]
        # start_view.no_team.extend(mock_users)

        await interaction.response.send_message(
            embed=Embed(
                title=messages.commands.game.setup,
                description=f"{GUIDE}\n\n" f"-# {messages.commands.game.setup_instructions}",
                color=Colors.teal,
            ),
            view=start_view,
        )

    @command(name="guide", description="Guide to the game.")
    async def guide(self, interaction: Interaction[Bot]) -> None:
        await interaction.response.send_message(
            embed=Embed(
                title="Codenames Guide",
                description=GUIDE,
                color=Colors.teal,
            )
        )

    @command(name="leaderboard", description="Show the Codenames leaderboard.")
    @describe(
        category="Category to show leaderboard for",
        limit="Number of players to show (default 10, max 20)",
    )
    @choices(
        category=[
            Choice(name="Overall", value="overall"),
            Choice(name="Captain", value="captain"),
            Choice(name="Team Player", value="team"),
        ]
    )
    async def leaderboard(
        self,
        interaction: Interaction[Bot],
        category: Literal["overall", "captain", "team"],
        limit: int = 10,
    ) -> None:
        await interaction.response.defer()

        # Validate and constrain the limit
        limit = max(1, min(limit, 20))  # Ensure limit is between 1 and 20
        if category == "overall":
            query = """
            SELECT id, games, wins, CAST(wins AS FLOAT) / games AS winrate
            FROM players
            WHERE games > 0
            ORDER BY winrate DESC, games DESC
            LIMIT ?
            """
        elif category == "captain":
            query = """
            SELECT id, games_cap AS games, wins_cap AS wins, CAST(wins_cap AS FLOAT) / games_cap AS winrate
            FROM players
            WHERE games_cap > 0
            ORDER BY winrate DESC, games_cap DESC
            LIMIT ?
            """
        else:  # team
            query = """
            SELECT id, (games - games_cap) AS games, (wins - wins_cap) AS wins, 
                   CAST((wins - wins_cap) AS FLOAT) / (games - games_cap) AS winrate
            FROM players
            WHERE (games - games_cap) > 0
            ORDER BY winrate DESC, (games - games_cap) DESC
            LIMIT ?
            """

        results = await self.bot.db.fetch(query, (limit,), fetchall=True)

        if not results:
            await interaction.followup.send("No data available for the leaderboard.")
            return

        embed = Embed(title=f"Leaderboard • {category.capitalize()}", color=Colors.teal)

        for i, (user_id, games, wins, winrate) in enumerate(results, start=1):
            user = await self.bot.fetch_user(user_id)
            user_name = user.global_name or user.display_name
            embed.add_field(
                name=f"{i}. {user_name}",
                value=f"Games: {games} • Wins: {wins} • Winrate: {winrate:.2%}",
                inline=False,
            )

        await interaction.followup.send(embed=embed)

    @command(description="Show player's statistics.")
    @describe(
        member="Server member whose statistics will be displayed",
    )
    async def stats(self, interaction: Interaction[Bot], member: Member | None = None) -> None:
        await interaction.response.defer()
        player = member or interaction.user
        name = f"**{player.global_name if player.global_name else player.display_name}**"

        if player == self.bot.user:
            embed = Embed(
                title=messages.commands.stats.smbs_stats.format(name),
                description=messages.commands.stats.egg_game_master_desc,
                color=Colors.teal,
            )

            await interaction.followup.send(embed=embed)
            return

        info = await self.bot.db.fetch(
            "SELECT date, games, games_cap, wins, wins_cap FROM players WHERE id = ?",
            (player.id,),
        )
        if not info:
            await send_error(
                interaction, messages.errors.title, messages.errors.never_played.format(name)
            )
            return

        date, games, games_cap, wins, wins_cap = info[0], *map(int, info[1:])
        games_tm = games - games_cap  # In the team
        wins_team = wins - wins_cap
        winrate = f"{round((wins / games) * 100)}%" if games else "-"
        winrate_cap = f"{round((wins_cap / games_cap) * 100)}%" if games_cap else "-"
        winrate_team = f"{round((wins_team / games_tm) * 100)}%" if games_tm else "-"

        embed = Embed(
            title=messages.commands.stats.smbs_stats.format(name),
            description=messages.commands.stats.playing_since.format(f"**{date}**"),
            color=Colors.teal,
        )
        embed.add_field(
            name=messages.commands.stats.total,
            value=f"{messages.commands.stats.games_played}: **{games}**\n{messages.commands.stats.games_won}: **{wins}**"
            f"\n{messages.commands.stats.winrate}: **{winrate}**",
        )
        embed.add_field(
            name=messages.commands.stats.team,
            value=f"{messages.commands.stats.games_played}: **{games_tm}**\n{messages.commands.stats.games_won}: **{wins_team}**"
            f"\n{messages.commands.stats.winrate}: **{winrate_team}**",
        )
        embed.add_field(
            name=messages.commands.stats.spymaster,
            value=f"{messages.commands.stats.games_played}: **{games_cap}**\n{messages.commands.stats.games_won}: **{wins_cap}**"
            f"\n{messages.commands.stats.winrate}: **{winrate_cap}**",
        )

        embed.add_field(name=EMPTY, value=messages.commands.stats.note, inline=False)
        embed.set_thumbnail(url=player.display_avatar)

        await interaction.followup.send(embed=embed)

    async def _build_team(
        self, channel: PartialMessageable, team: list[User | Member], color: str
    ) -> tuple[Member, list[Member]]:
        cap_selection_list = map(
            lambda letter, player: f"**{letter}** - {player.mention}", ALPHABET, team
        )
        cap_msg = await channel.send(
            embed=Embed(
                title=messages.commands.start.spy_selection_title.format(color),
                description=messages.commands.start.spy_selection_desc.format(
                    "\n".join(cap_selection_list)
                ),
                color=Colors.red if color == messages.game.red else Colors.blue,
            )
        )
        await cap_msg.add_reaction(REACTION_R)
        for r_letter in REACTION_ALPHABET[: len(team)]:
            await cap_msg.add_reaction(r_letter)
        await asyncio.sleep(15)

        new_cap_msg = await channel.fetch_message(cap_msg.id)
        emojis = await most_count_reaction_emojis(new_cap_msg, team)

        if REACTION_R in emojis:
            captain = random.choice(team)
        else:
            potential_caps = map(lambda e: team[REACTION_ALPHABET.index(e)], emojis)
            captain = random.choice(tuple(potential_caps))

        players_left = team.copy()
        players_left.remove(captain)

        await channel.send(
            embed=Embed(
                title=messages.commands.start.spy_selected_title.format(color),
                description=messages.commands.start.spy_selected_desc.format(captain.mention),
                color=Colors.red if color == messages.game.red else Colors.blue,
            )
        )
        return cast(Member, captain), cast(list[Member], players_left)

    async def _fetch_roles_object(self, interaction: Interaction) -> tuple[Role, Role, Role, Role]:
        guild = cast(Guild, interaction.guild)
        blue_team_role = cast(Role, guild.get_role(CODENAMES_BLUE_TEAM_ROLE))
        red_team_role = cast(Role, guild.get_role(CODENAMES_RED_TEAM_ROLE))

        blue_captain_role = cast(Role, guild.get_role(CODENAMES_BLUE_SPYMASTER_ROLE))
        red_captain_role = cast(Role, guild.get_role(CODENAMES_RED_SPYMASTER_ROLE))
        return blue_team_role, red_team_role, blue_captain_role, red_captain_role

    async def _clear_roles(
        self,
        red_captain_role: Role,
        red_team_role: Role,
        blue_captain_role: Role,
        blue_team_role: Role,
    ) -> None:
        for role in [red_captain_role, red_team_role, blue_captain_role, blue_team_role]:
            for member in role.members:
                await member.remove_roles(role)

    async def _start(
        self,
        interaction: Interaction,
        team1: list[User | Member],
        team2: list[User | Member],
        dictionary: str,
    ) -> None:
        uuid = str(get_uuid())

        channel = self.bot.get_partial_messageable(
            interaction.channel_id,  # pyright: ignore[reportArgumentType]
            guild_id=interaction.guild_id,
        )

        # Build teams
        team1_cap, team1_pl = await self._build_team(channel, team1, messages.game.red)
        team2_cap, team2_pl = await self._build_team(channel, team2, messages.game.blue)

        # Fetch role objects
        (
            blue_team_role,
            red_team_role,
            blue_captain_role,
            red_captain_role,
        ) = await self._fetch_roles_object(interaction)

        # remove roles from members first
        await self._clear_roles(red_captain_role, red_team_role, blue_captain_role, blue_team_role)

        # Assign roles to the teams
        await team1_cap.add_roles(red_captain_role)
        for player in team1_pl:
            await player.add_roles(red_team_role)
        await team2_cap.add_roles(blue_captain_role)
        for player in team2_pl:
            await player.add_roles(blue_team_role)

        # Notifying everyone of their teams and captains in one embed
        await channel.send(
            embeds=[
                Embed(
                    title=messages.game.start_announcement,
                    description=messages.game.start_announcement_desc,
                    color=Colors.teal,
                ),
                Embed(
                    title=messages.game.start_notification_title.format(messages.game.red),
                    description=messages.game.start_notification_desc.format(
                        team1_cap.mention, "\n".join(map(lambda p: p.mention, team1_pl))
                    ),
                    color=Colors.red,
                ),
                Embed(
                    title=messages.game.start_notification_title.format(messages.game.blue),
                    description=messages.game.start_notification_desc.format(
                        team2_cap.mention, "\n".join(map(lambda p: p.mention, team2_pl))
                    ),
                    color=Colors.blue,
                ),
            ]
        )

        (
            team_red_words,
            team_blue_words,
            endgame_word,
            no_team_words,
            available_words,
        ) = await gen.words(dictionary)

        opened_words = []
        order = available_words.copy()  # Has to be a list
        random.shuffle(order)
        order = tuple(order)

        if len(team_red_words) > len(team_blue_words):
            current_color = messages.game.red
            current_cap = team1_cap
            current_pl = team1_pl
            current_words = team_red_words
            other_color = messages.game.blue
            other_cap = team2_cap
            other_pl = team2_pl
            other_words = team_blue_words
        else:
            current_color = messages.game.blue
            current_cap = team2_cap
            current_pl = team2_pl
            current_words = team_blue_words
            other_color = messages.game.red
            other_cap = team1_cap
            other_pl = team1_pl
            other_words = team_red_words

        # Main game loop
        game_running = True
        first_round = True
        send_field_to_caps = True
        while game_running:
            gen.field(
                team_red_words,
                team_blue_words,
                endgame_word,
                no_team_words,
                opened_words,
                order,
                uuid,
            )
            await send_fields(uuid, channel, current_cap, other_cap, send_field_to_caps)
            send_field_to_caps = True

            if first_round:
                shutil.copy(Paths.cap_img(uuid), Paths.cap_img_init(uuid))
                first_round = False

            await channel.send(
                embed=Embed(
                    title=messages.game.waiting_title.format(current_color),
                    description=messages.game.waiting_desc_spy.format(current_cap.mention),
                    color=Colors.red if current_color == messages.game.red else Colors.blue,
                )
            )
            await current_cap.send(
                embed=Embed(
                    title=messages.game.spy_move_request_title,
                    description=messages.game.spy_move_request_desc,
                    color=Colors.red if current_color == messages.game.red else Colors.blue,
                )
            )

            move_msg = await self.bot.wait_for(  # type: ignore
                "message",
                check=lambda msg: msg.channel == current_cap.dm_channel  # type: ignore
                and re.fullmatch(r"\w+ \d+", msg.content)
                and not msg.content.endswith(" 0"),
            )
            move = move_msg.content
            word_count = int(move.split()[-1])

            await current_cap.send(
                embed=Embed(
                    title=messages.game.spy_move_accepted,
                    color=Colors.red if current_color == messages.game.red else Colors.blue,
                )
            )
            await channel.send(
                embeds=[
                    Embed(
                        title=messages.game.spy_move_notification_title.format(current_color),
                        description=messages.game.spy_move_notification_desc.format(
                            current_cap.mention, move
                        ),
                        color=Colors.red if current_color == messages.game.red else Colors.blue,
                    ),
                    Embed(
                        title=messages.game.waiting_title.format(current_color),
                        description=f"{messages.game.waiting_desc_pl.format(current_color)}\n{messages.game.pl_move_instructions}",
                        color=Colors.red if current_color == messages.game.red else Colors.blue,
                    ),
                ]
            )
            while word_count >= 0:
                # >= because of the rule that the team can open one more word than their captain intended
                move_msg = await self.bot.wait_for(
                    "message",
                    check=lambda msg: (
                        msg.channel.id == channel.id
                        and msg.author in current_pl
                        and (msg.content.lower() in available_words or msg.content == "0")
                    )
                    or (msg.content == "000" and msg.author in team1 + team2),
                )
                move = move_msg.content.lstrip().lower().replace("ё", "е")  # noqa: RUF001

                if move == "0":
                    await move_msg.add_reaction("🆗")
                    send_field_to_caps = False
                    break
                if move == "000":
                    stop_msg = await move_msg.reply(
                        embed=Embed(
                            title=messages.game.voting_for_stopping_title,
                            description=messages.game.voting_for_stopping_desc,
                            color=Colors.teal,
                        )
                    )

                    yes, no = await vote(stop_msg, 15, team1 + team2)
                    if yes > no:
                        await stop_msg.edit(content=messages.game.game_stopped)

                        game_running = False
                        break
                    else:
                        await stop_msg.edit(
                            content=messages.game.game_continued,
                        )

                        continue  # No need to generate a new field or decrease word_count

                opened_words.append(move)
                available_words.remove(move)
                gen.field(
                    team_red_words,
                    team_blue_words,
                    endgame_word,
                    no_team_words,
                    opened_words,
                    order,
                    uuid,
                )

                if move in no_team_words:
                    await move_msg.reply(
                        embed=Embed(
                            title=messages.game.miss_title,
                            description=messages.game.miss_desc_no_team_guild,
                            color=Colors.white,
                        )
                    )
                    await current_cap.send(
                        embed=Embed(
                            title=messages.game.miss_title,
                            description=messages.game.miss_desc_no_team_dm.format(move),
                            color=Colors.white,
                        )
                    )
                    await other_cap.send(
                        embed=Embed(
                            title=messages.game.opponents_miss_title,
                            description=messages.game.opponents_miss_desc.format(move),
                            color=Colors.white,
                        )
                    )
                    break

                elif move in other_words:
                    await move_msg.reply(
                        embed=Embed(
                            title=messages.game.miss_title,
                            description=messages.game.miss_desc_other_team_guild,
                            color=Colors.red if other_color == messages.game.red else Colors.blue,
                        )
                    )
                    await current_cap.send(
                        embed=Embed(
                            title=messages.game.miss_title,
                            description=messages.game.miss_desc_other_team_dm.format(move),
                            color=Colors.red if other_color == messages.game.red else Colors.blue,
                        )
                    )
                    await other_cap.send(
                        embed=Embed(
                            title=messages.game.lucky_title,
                            description=messages.game.lucky_desc_your_team.format(move),
                            color=Colors.red if other_color == messages.game.red else Colors.blue,
                        )
                    )

                    if set(other_words) <= set(opened_words):  # If all second_words are opened
                        await send_fields(uuid, channel, current_cap, other_cap)

                        await channel.send(
                            embed=Embed(
                                title=messages.game.game_over_title,
                                description=messages.game.game_over_desc_all.format(other_color),
                                color=Colors.red
                                if other_color == messages.game.red
                                else Colors.blue,
                            )
                        )

                        await current_cap.send(
                            embed=Embed(
                                title=messages.game.your_team_lost_title,
                                description=messages.game.your_team_lost_desc,
                                color=Colors.red
                                if other_color == messages.game.red
                                else Colors.blue,
                            )
                        )
                        await self.bot.db.increase_stats(current_cap.id, ("games", "games_cap"))
                        for player in current_pl:
                            await player.send(
                                embed=Embed(
                                    title=messages.game.your_team_lost_title,
                                    description=messages.game.your_team_lost_desc,
                                    color=Colors.red
                                    if other_color == messages.game.red
                                    else Colors.blue,
                                )
                            )
                            await self.bot.db.increase_stats(player.id, ("games",))

                        await other_cap.send(
                            embed=Embed(
                                title=messages.game.your_team_won_title,
                                description=messages.game.your_team_won_desc,
                                color=Colors.red
                                if other_color == messages.game.red
                                else Colors.blue,
                            )
                        )
                        await self.bot.db.increase_stats(
                            other_cap.id, ("games", "games_cap", "wins", "wins_cap")
                        )
                        for player in other_pl:
                            await player.send(
                                embed=Embed(
                                    title=messages.game.your_team_won_title,
                                    description=messages.game.your_team_won_desc,
                                    color=Colors.red
                                    if other_color == messages.game.red
                                    else Colors.blue,
                                )
                            )
                            await self.bot.db.increase_stats(player.id, ("games", "wins"))

                        game_running = False
                        break

                    break
                elif move == endgame_word:
                    await move_msg.reply(
                        embed=Embed(
                            title=messages.game.miss_title,
                            description=messages.game.miss_desc_endgame_guild,
                            color=Colors.black,
                        )
                    )
                    await current_cap.send(
                        embed=Embed(
                            title=messages.game.miss_title,
                            description=messages.game.miss_desc_endgame_dm.format(move),
                            color=Colors.black,
                        )
                    )
                    await other_cap.send(
                        embed=Embed(
                            title=messages.game.lucky_title,
                            description=messages.game.lucky_desc_endgame.format(move),
                            color=Colors.black,
                        )
                    )

                    await send_fields(uuid, channel, current_cap, other_cap)

                    await channel.send(
                        embed=Embed(
                            title=messages.game.game_over_title,
                            description=messages.game.game_over_desc_endgame.format(
                                other_color, current_color
                            ),
                            color=Colors.red if other_color == messages.game.red else Colors.blue,
                        )
                    )

                    await current_cap.send(
                        embed=Embed(
                            title=messages.game.your_team_lost_title,
                            description=messages.game.your_team_lost_desc,
                            color=Colors.red if other_color == messages.game.red else Colors.blue,
                        )
                    )
                    await self.bot.db.increase_stats(current_cap.id, ("games", "games_cap"))
                    for player in current_pl:
                        await player.send(
                            embed=Embed(
                                title=messages.game.your_team_lost_title,
                                description=messages.game.your_team_lost_desc,
                                color=Colors.red
                                if other_color == messages.game.red
                                else Colors.blue,
                            )
                        )
                        await self.bot.db.increase_stats(player.id, ("games",))

                    await other_cap.send(
                        embed=Embed(
                            title=messages.game.your_team_won_title,
                            description=messages.game.your_team_won_desc,
                            color=Colors.red if other_color == messages.game.red else Colors.blue,
                        )
                    )
                    await self.bot.db.increase_stats(
                        other_cap.id, ("games", "games_cap", "wins", "wins_cap")
                    )
                    for player in other_pl:
                        await player.send(
                            embed=Embed(
                                title=messages.game.your_team_won_title,
                                description=messages.game.your_team_won_desc,
                                color=Colors.red
                                if other_color == messages.game.red
                                else Colors.blue,
                            )
                        )
                        await self.bot.db.increase_stats(player.id, ("games", "wins"))

                    game_running = False
                    break
                else:  # They guessed
                    await move_msg.reply(
                        embed=Embed(
                            title=messages.game.success_title,
                            description=messages.game.success_desc_guild,
                            color=Colors.red if current_color == messages.game.red else Colors.blue,
                        )
                    )
                    await current_cap.send(
                        embed=Embed(
                            title=messages.game.success_title,
                            description=messages.game.success_desc_dm.format(move),
                            color=Colors.red if current_color == messages.game.red else Colors.blue,
                        )
                    )
                    await other_cap.send(
                        embed=Embed(
                            title=messages.game.opponents_success_title,
                            description=messages.game.opponents_success_desc.format(move),
                            color=Colors.red if current_color == messages.game.red else Colors.blue,
                        )
                    )

                    if set(current_words) <= set(opened_words):  # If all first_words are opened
                        await send_fields(uuid, channel, current_cap, other_cap)

                        await channel.send(
                            embed=Embed(
                                title=messages.game.game_over_title,
                                description=messages.game.game_over_desc_all.format(current_color),
                                color=Colors.red
                                if current_color == messages.game.red
                                else Colors.blue,
                            )
                        )

                        await current_cap.send(
                            embed=Embed(
                                title=messages.game.your_team_won_title,
                                description=messages.game.your_team_won_desc,
                                color=Colors.red
                                if current_color == messages.game.red
                                else Colors.blue,
                            )
                        )
                        await self.bot.db.increase_stats(
                            current_cap.id, ("games", "games_cap", "wins", "wins_cap")
                        )
                        for player in current_pl:
                            await player.send(
                                embed=Embed(
                                    title=messages.game.your_team_won_title,
                                    description=messages.game.your_team_won_desc,
                                    color=Colors.red
                                    if current_color == messages.game.red
                                    else Colors.blue,
                                )
                            )
                            await self.bot.db.increase_stats(player.id, ("games", "wins"))

                        await other_cap.send(
                            embed=Embed(
                                title=messages.game.your_team_lost_title,
                                description=messages.game.your_team_lost_desc,
                                color=Colors.red
                                if current_color == messages.game.red
                                else Colors.blue,
                            )
                        )
                        await self.bot.db.increase_stats(other_cap.id, ("games", "games_cap"))
                        for player in other_pl:
                            await player.send(
                                embed=Embed(
                                    title=messages.game.your_team_lost_title,
                                    description=messages.game.your_team_lost_desc,
                                    color=Colors.red
                                    if current_color == messages.game.red
                                    else Colors.blue,
                                )
                            )
                            await self.bot.db.increase_stats(player.id, ("games",))

                        game_running = False
                        break

                    if (
                        word_count > 0
                    ):  # If quitting after this move, field will be sent twice in a row
                        await send_fields(uuid, channel, current_cap, other_cap)

                word_count -= 1

            current_color, other_color = other_color, current_color
            current_cap, other_cap = other_cap, current_cap
            current_pl, other_pl = other_pl, current_pl
            current_words, other_words = other_words, current_words

        # Clear roles
        await self._clear_roles(red_captain_role, red_team_role, blue_captain_role, blue_team_role)

        # Sending initial captain filed to the guild text channel
        await channel.send(
            file=File(Paths.cap_img_init(uuid), filename="initial_captain_field.png")
        )

        os.remove(Paths.pl_img(uuid))
        os.remove(Paths.cap_img(uuid))
        os.remove(Paths.cap_img_init(uuid))


async def setup(bot: Bot) -> None:
    await bot.add_cog(Codenames(bot))
