import random
from collections.abc import Iterable, Sequence

import aiofiles
from PIL import Image, ImageDraw

from bot.core.codenames.constants import Colors, FieldSizing, Paths, big_font, font

FIRST_TEAM_WORD_COUNT = 9
SECOND_TEAM_WORD_COUNT = 8


def field(
    team1_words: Iterable[str],
    team2_words: Iterable[str],
    endgame_word: str,
    no_team_words: Iterable[str],
    opened_words: Iterable[str],
    order: Sequence[str],
    uuid: str,
) -> None:
    """Creates and saves captain and player fields as images from the given game word lists.

    :param team1_words: Red cards
    :param team2_words: Blue cards
    :param endgame_word: Black card
    :param no_team_words: White cards
    :param opened_words: "Used" words
    :param order: Order that the words should be displayed in
    :param game_uuid: Game uuid to save images without conflicts
    :return: None
    """
    img = Image.new("RGB", (FieldSizing.width, FieldSizing.height), Colors.background)
    draw = ImageDraw.Draw(img)

    # Drawing two bottom rectangles with left words counter
    draw.rectangle(
        xy=(
            0,
            FieldSizing.height - FieldSizing.footer_height,
            FieldSizing.width / 2 - 1,
            FieldSizing.height - 1,
        ),
        fill=Colors.red_fill,
    )
    red_words_left = 0
    for word in team1_words:
        if word not in opened_words:
            red_words_left += 1
    draw.text(
        xy=(FieldSizing.width / 4, FieldSizing.height - FieldSizing.footer_height / 2),
        text=str(red_words_left),
        fill=Colors.red_font,
        font=big_font,
        anchor=FieldSizing.text_anchor,
    )

    draw.rectangle(
        xy=(
            FieldSizing.width / 2,
            FieldSizing.height - FieldSizing.footer_height,
            FieldSizing.width - 1,
            FieldSizing.height - 1,
        ),
        fill=Colors.blue_fill,
    )
    blue_words_left = 0
    for word in team2_words:
        if word not in opened_words:
            blue_words_left += 1
    draw.text(
        xy=(
            FieldSizing.width / 2 + FieldSizing.width / 4,
            FieldSizing.height - FieldSizing.footer_height / 2,
        ),
        text=str(blue_words_left),
        fill=Colors.blue_font,
        font=big_font,
        anchor=FieldSizing.text_anchor,
    )

    # Creating two separate images for two fields
    cap_img = img.copy()
    cap_draw = ImageDraw.Draw(cap_img)
    pl_img = img.copy()
    pl_draw = ImageDraw.Draw(pl_img)

    fill_col: tuple[int, int, int] = Colors.neutral_fill
    outline_col: tuple[int, int, int] = Colors.neutral_outline
    font_col: tuple[int, int, int] = Colors.neutral_font

    # Filling the captain's field
    for x in range(FieldSizing.card_count):
        for y in range(FieldSizing.card_count):
            word = order[x * FieldSizing.card_count + y]
            if word in team1_words:
                if word in opened_words:
                    fill_col = Colors.red_opened_fill
                    outline_col = Colors.red_opened_fill
                    font_col = Colors.red_opened_font
                else:
                    fill_col = Colors.red_fill
                    outline_col = Colors.red_fill
                    font_col = Colors.red_font
            elif word in team2_words:
                if word in opened_words:
                    fill_col = Colors.blue_opened_fill
                    outline_col = Colors.blue_opened_fill
                    font_col = Colors.blue_opened_font
                else:
                    fill_col = Colors.blue_fill
                    outline_col = Colors.blue_fill
                    font_col = Colors.blue_font
            elif word == endgame_word:
                if word in opened_words:
                    fill_col = Colors.black_opened_fill
                    outline_col = Colors.black_opened_fill
                    font_col = Colors.black_opened_font
                else:
                    fill_col = Colors.black_fill
                    outline_col = Colors.black_fill
                    font_col = Colors.black_font
            elif word in no_team_words:
                if word in opened_words:
                    fill_col = Colors.neutral_opened_cap_fill
                    outline_col = Colors.neutral_opened_cap_outline
                    font_col = Colors.neutral_opened_cap_font
                else:
                    fill_col = Colors.neutral_fill
                    outline_col = Colors.neutral_outline
                    font_col = Colors.neutral_font

            cap_draw.rounded_rectangle(
                xy=(
                    FieldSizing.card_spacing * (x + 1) + FieldSizing.card_width * x,
                    FieldSizing.card_spacing * (y + 1) + FieldSizing.card_height * y,
                    (FieldSizing.card_spacing + FieldSizing.card_width) * (x + 1),
                    (FieldSizing.card_spacing + FieldSizing.card_height) * (y + 1),
                ),
                radius=FieldSizing.card_radius,
                fill=fill_col,
                outline=outline_col,
                width=FieldSizing.card_outline_width,
            )

            cap_draw.text(
                xy=(
                    FieldSizing.card_spacing * (x + 1)
                    + FieldSizing.card_width * x
                    + FieldSizing.card_width / 2,
                    FieldSizing.card_spacing * (y + 1)
                    + FieldSizing.card_height * y
                    + FieldSizing.card_height / 2,
                ),
                text=str(word).upper(),
                fill=font_col,
                font=font,
                anchor=FieldSizing.text_anchor,
            )

    # Filling the players' field
    for x in range(FieldSizing.card_count):
        for y in range(FieldSizing.card_count):
            word = order[x * FieldSizing.card_count + y]
            if word in opened_words:
                if word in team1_words:
                    fill_col = Colors.red_fill
                    outline_col = Colors.red_fill
                    font_col = Colors.red_font
                elif word in team2_words:
                    fill_col = Colors.blue_fill
                    outline_col = Colors.blue_fill
                    font_col = Colors.blue_font
                elif word == endgame_word:
                    fill_col = Colors.black_fill
                    outline_col = Colors.black_fill
                    font_col = Colors.black_font
                elif word in no_team_words:
                    fill_col = Colors.neutral_opened_pl_fill
                    outline_col = Colors.neutral_opened_pl_outline
                    font_col = Colors.neutral_opened_pl_font
            else:
                fill_col = Colors.neutral_fill
                outline_col = Colors.neutral_outline
                font_col = Colors.neutral_font

            pl_draw.rounded_rectangle(
                xy=(
                    FieldSizing.card_spacing * (x + 1) + FieldSizing.card_width * x,
                    FieldSizing.card_spacing * (y + 1) + FieldSizing.card_height * y,
                    (FieldSizing.card_spacing + FieldSizing.card_width) * (x + 1),
                    (FieldSizing.card_spacing + FieldSizing.card_height) * (y + 1),
                ),
                radius=FieldSizing.card_radius,
                fill=fill_col,
                outline=outline_col,
                width=FieldSizing.card_outline_width,
            )

            pl_draw.text(
                xy=(
                    FieldSizing.card_spacing * (x + 1)
                    + FieldSizing.card_width * x
                    + FieldSizing.card_width / 2,
                    FieldSizing.card_spacing * (y + 1)
                    + FieldSizing.card_height * y
                    + FieldSizing.card_height / 2,
                ),
                text=str(word).upper(),
                fill=font_col,
                font=font,
                anchor=FieldSizing.text_anchor,
            )

    cap_img.save(Paths.cap_img(uuid))
    pl_img.save(Paths.pl_img(uuid))


async def words(dict_name: str) -> tuple[list[str], list[str], str, list[str], list[str]]:
    """Returns game words randomly picked from the given dictionary.

    :param dict_name: Dictionary name
    :return: Game words: red (list), blue (list), endgame (str), no team (list), available words (list)
    """
    async with aiofiles.open(Paths.dictionary(dict_name), "r", encoding="utf-8") as dictionary:
        dict_words = (await dictionary.read()).lstrip().lower().replace("ё", "е").split("\n")  # noqa: RUF001
    words: set[str] = set(random.sample(dict_words, 25))

    endgame_word: str = random.choice(tuple(words))
    words.remove(endgame_word)

    if bool(random.randint(0, 1)):
        team1_words: list[str] = random.sample(tuple(words), FIRST_TEAM_WORD_COUNT)  # type: ignore
        words.difference_update(team1_words)
        team2_words: list[str] = random.sample(tuple(words), SECOND_TEAM_WORD_COUNT)  # type: ignore
        no_team_words: list[str] = list(words.difference(team2_words))  # type: ignore
    else:
        team2_words: list[str] = random.sample(tuple(words), FIRST_TEAM_WORD_COUNT)
        words.difference_update(team2_words)
        team1_words: list[str] = random.sample(tuple(words), SECOND_TEAM_WORD_COUNT)
        no_team_words: list[str] = list(words.difference(team1_words))

    available_words: list[str] = list(team1_words + team2_words + [endgame_word] + no_team_words)

    print("Dictionary", dict_name, "loaded.")
    print(
        "Team 1 words:",
        team1_words,
        "\nTeam 2 words:",
        team2_words,
        "\nEndgame word:",
        endgame_word,
        "\nNo team words:",
        no_team_words,
        "\nAll words:",
        available_words,
    )
    return team1_words, team2_words, endgame_word, no_team_words, available_words


# Mock field generation
if __name__ == "__main__":
    import asyncio

    team_red_words, team_blue_words, endgame_word, no_team_words, available_words = asyncio.run(
        words("std")
    )

    order = available_words.copy()  # Has to be a list
    random.shuffle(order)
    order = tuple(order)

    field(
        team_red_words,
        team_blue_words,
        endgame_word,
        no_team_words,
        no_team_words,
        order,
        "test",
    )
