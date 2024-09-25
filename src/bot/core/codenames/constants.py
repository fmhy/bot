from pathlib import Path

from discord import Color
from PIL import ImageFont

EMPTY = "\u2063"  # invisible separator

GUIDE = """\n
Codenames is a word guessing game that can be played with 2 teams of 2+ players.
* Every team has a spymaster and operatives.
* Each team has 8/9 cards that belong to them, and the spymaster's job is to give one word clues that point their operatives to the correct cards.
* The operatives can guess the card by simply typing the name of it.
* **The clues must be one word only and must not contain the names of cards.**
* There is also a black card (Assassin) which, if guessed, ends the game and results in a win for the other team.
* Guessing white cards results in your team's turn being over.
"""

CODENAMES_ROLE = 1282437850255855706
CODENAMES_CHANNEL = 1282419113381331019
CODENAMES_BLUE_TEAM_ROLE = 1282441675435802741
CODENAMES_RED_TEAM_ROLE = 1282441678866747483
CODENAMES_BLUE_SPYMASTER_ROLE = 1282441667961688196
CODENAMES_RED_SPYMASTER_ROLE = 1282441671669321769

ALPHABET = "ABCDEFGHIJKLMNOPQSTUVWXYZ"  # Without letter R
REACTION_ALPHABET = "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇸🇹🇺🇻🇼🇽🇾🇿"  # Without R too
REACTION_R = "🇷"
REACTION_NUMBERS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣")


font = ImageFont.truetype(
    str(Path("data", "fonts", "RobotoCondensed-Bold.ttf")), 80, encoding="utf-8"
)
big_font = ImageFont.truetype(str(Path("data", "fonts", "Roboto-Bold.ttf")), 350, encoding="utf-8")


dictionaries = {
    "std": "Original English (400 words)",
    "duet": "Original Duet (400 words)",
    "deep": "Original Deep Undercover (18+, 390 words)",
    "enlarged": "Enlarged English (763 words)",
    "enlarged18": "Enlarged English (18+, 1081 words)",
    "all": "All English dictionaries (18+, 1139 words)",
    "esp": "Esperanto",
    "custom_words": "Custom Piracy words",
}


class Paths:
    img_dir = Path("state", "images")
    db = Path("state", "database.db")

    @classmethod
    def cap_img(cls, game_uuid: str) -> Path:
        return Path(cls.img_dir, f"{game_uuid}-spymaster.png")

    @classmethod
    def cap_img_init(cls, game_uuid: str) -> Path:
        return Path(cls.img_dir, f"{game_uuid}-spymaster-initial.png")

    @classmethod
    def pl_img(cls, game_uuid: str) -> Path:
        return Path(cls.img_dir, f"{game_uuid}-player.png")

    @staticmethod
    def dictionary(name: str) -> Path:
        return Path("data", "dictionaries", f"{name}.txt")


class FieldSizing:
    width = 3840
    height = 2160

    text_anchor = "mm"  # Middle of the rectangle

    footer_height = 400

    card_count = 5
    card_spacing = 50
    card_width = (width - (card_spacing * (card_count + 1))) / card_count
    card_height = (height - footer_height - (card_spacing * (card_count + 1))) / card_count
    card_radius = 10
    card_outline_width = 2


class Colors:
    teal = Color.teal()
    red = Color.from_rgb(255, 100, 80)
    blue = Color.from_rgb(80, 187, 255)
    white = Color.from_rgb(220, 220, 220)
    black = Color.from_rgb(34, 34, 34)
    background = (18, 18, 18)

    red_fill = (255, 100, 80)
    red_font = (136, 16, 0)
    red_opened_fill = (255, 223, 219)
    red_opened_font = red_font

    blue_fill = (80, 187, 255)
    blue_font = (0, 84, 138)
    blue_opened_fill = (219, 241, 255)
    blue_opened_font = blue_font

    black_fill = (40, 40, 40)
    black_font = (169, 169, 169)
    black_opened_fill = (20, 20, 20)
    black_opened_font = (105, 105, 105)

    # Neutral (no team) card colors
    neutral_fill = (60, 60, 60)
    neutral_outline = (80, 80, 80)
    neutral_font = (200, 200, 200)
    neutral_opened_cap_fill = (40, 40, 40)
    neutral_opened_cap_outline = (70, 70, 70)
    neutral_opened_cap_font = (160, 160, 160)
    neutral_opened_pl_fill = (25, 25, 25)
    neutral_opened_pl_outline = neutral_opened_pl_fill
    neutral_opened_pl_font = (190, 190, 190)
