from dataclasses import dataclass


@dataclass
class Game:
    red: str
    blue: str

    start_announcement: str
    start_announcement_desc: str
    start_notification_title: str
    start_notification_desc: str

    waiting_title: str
    waiting_desc_spy: str
    waiting_desc_pl: str
    pl_move_instructions: str

    spy_move_request_title: str
    spy_move_request_desc: str
    spy_move_accepted: str
    spy_move_notification_title: str
    spy_move_notification_desc: str

    success_title: str
    success_desc_guild: str
    success_desc_dm: str
    opponents_success_title: str
    opponents_success_desc: str

    miss_title: str
    miss_desc_other_team_guild: str
    miss_desc_other_team_dm: str
    miss_desc_no_team_guild: str
    miss_desc_no_team_dm: str
    miss_desc_endgame_guild: str
    miss_desc_endgame_dm: str
    opponents_miss_title: str
    opponents_miss_desc: str  # Only for no_team reason

    lucky_title: str
    lucky_desc_your_team: str
    lucky_desc_endgame: str

    game_over_title: str
    game_over_desc_all: str
    game_over_desc_endgame: str
    your_team_won_title: str
    your_team_won_desc: str
    your_team_lost_title: str
    your_team_lost_desc: str

    voting_for_stopping_title: str
    voting_for_stopping_desc: str
    game_stopped: str
    game_continued: str


@dataclass
class GameCommand:
    setup: str
    setup_instructions: str
    setup_over: str
    setup_cancelled: str
    team_red: str
    team_blue: str
    random: str
    empty_list: str


@dataclass
class StartCommand:
    spy_selection_title: str
    spy_selection_desc: str
    spy_selected_title: str
    spy_selected_desc: str


@dataclass
class StatsCommand:
    smbs_stats: str
    playing_since: str
    total: str
    spymaster: str
    team: str
    games_played: str
    games_won: str
    winrate: str
    note: str
    egg_game_master_desc: str


@dataclass
class Commands:
    game: GameCommand
    start: StartCommand
    stats: StatsCommand


@dataclass
class UI:
    alert: str
    confirm: str
    cancel: str
    random: str
    leave: str
    start_game: str
    cancel_reg: str


@dataclass
class HelpAndBrief:
    help: str
    brief: str = None  # type: ignore

    def __post_init__(self) -> None:
        self.brief = self.brief or self.help


@dataclass
class Errors:
    title: str
    not_host: str
    not_registered: str
    not_enough_players: str
    too_many_players: str
    never_played: str


@dataclass
class Messages:
    game: Game
    commands: Commands
    ui: UI
    errors: Errors


messages = Messages(
    game=Game(
        red="Red 🟥",
        blue="Blue 🟦",
        start_announcement="GAME STARTED!",
        start_announcement_desc="The game has started!",
        start_notification_title="Players of **{}** team",
        start_notification_desc="**Spymaster**: {}\n\nOperatives:\n{}",
        waiting_title="Waiting for move of **{}** team",
        waiting_desc_spy="Spymaster {} will make a move",
        waiting_desc_pl="Operatives of **{}** team",
        pl_move_instructions="-# Type words you want to open in response messages.\n"
        "-# To **FINISH THE MOVE** type **`0`**\n"
        "-# To **STOP THE GAME** type **`000`**",
        spy_move_request_title="Your turn",
        spy_move_request_desc="Type a word and a number in response message, for example: **`meow 3`**",
        spy_move_accepted="Move accepted",
        spy_move_notification_title="Spymaster of **{}** team has made a move",
        spy_move_notification_desc="{} says:\n**`{}`**",
        success_title="Success!",
        success_desc_guild="You guessed!",
        success_desc_dm="Your team opened the word **`{}`** that **belongs to them**!",
        opponents_success_title="Opponent's success",
        opponents_success_desc="The opponent team opened the word **`{}`** that **belongs to them**",
        miss_title="Miss",
        miss_desc_other_team_guild="Unfortunately, this word **belongs to the opponent team**",
        miss_desc_other_team_dm="Your team opened the word **`{}`** that **belongs to the opponent team**",
        miss_desc_no_team_guild="Unfortunately, this word **doesn't belong to any team**",
        miss_desc_no_team_dm="Your team opened the word **`{}`** that **doesn't belong to any team**",
        miss_desc_endgame_guild="Unfortunately, this word **is an endgame one**",
        miss_desc_endgame_dm="Your team opened the word **`{}`** that **is an endgame one**",
        opponents_miss_title="Opponent's miss",
        opponents_miss_desc="The opponent team opened the word **`{}`** that **doesn't belong to any team**",
        lucky_title="Lucky!",
        lucky_desc_your_team="The opponent team opened the word **`{}`** that **belongs to your team**",
        lucky_desc_endgame="The opponent team opened the word **`{}`** that **is an endgame one**",
        game_over_title="Game over!",
        game_over_desc_all="**{} team won!**\nThey opened all their words",
        game_over_desc_endgame="**{} team won!**\n{} team opened an endgame word",
        your_team_won_title="Your team won!",
        your_team_won_desc="Keep it up!",
        your_team_lost_title="Your team lost!",
        your_team_lost_desc="Good luck in the next game!",
        voting_for_stopping_title="Stopping the game",
        voting_for_stopping_desc="**Do you really want to stop playing?**\n\nAll players have 15 seconds to vote.",
        game_stopped="Majority of players voted for game stopping.",
        game_continued="Majority of players voted against game stopping.",
    ),
    commands=Commands(
        game=GameCommand(
            setup="Setup",
            setup_instructions="Register by clicking one of the buttons in the first row.",
            setup_over="Registration is over",
            setup_cancelled="The game has been cancelled.",
            team_red="Team Red 🟥",
            team_blue="Team Blue 🟦",
            random="Random (randomly spread across teams)",
            empty_list="Nobody is ready to play :(",
        ),
        start=StartCommand(
            spy_selection_title="**{}** team: Voting for the spymaster",
            spy_selection_desc="**R** - Random spymaster\n\n{}\n\nYou have 15 seconds to vote.",
            spy_selected_title="**{}** team: Spymaster selected",
            spy_selected_desc="Your spymaster is {}",
        ),
        stats=StatsCommand(
            smbs_stats="{}'s statistics",
            playing_since="Playing Codenames since {}",
            total="Total",
            spymaster="As spymaster",
            team="In the team",
            games_played="Games played",
            games_won="Games won",
            winrate="Winrate",
            note="Codenames is a **team game**, so the win-rate statistics **do not** exactly reflect player's skill.",
            egg_game_master_desc="Best game master: **100%**",
        ),
    ),
    ui=UI(
        alert="Are you sure you want to **{}**?",
        confirm="Confirm",
        cancel="Cancel",
        random="Random",
        leave="Leave",
        start_game="Start",
        cancel_reg="Cancel",
    ),
    errors=Errors(
        title="Error",
        not_registered="Not registered for the game.",
        not_enough_players="**Not enough players**\n**Each** team must have **at least 2** players.",
        too_many_players="**Too much players**\n**Each** team must have **no more than 25** players.",
        never_played="{} haven't played Codenames yet",
        not_host="You do not have the host role.",
    ),
)
