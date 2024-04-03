import asyncio
import functools
import json
import random
import urllib.parse
from io import BytesIO, StringIO
from typing import Any, Optional

from aiohttp import FormData
from aiohttp.client import ClientSession
from discord import Attachment, File, Interaction, app_commands
import discord
from discord.app_commands import Choice
from discord.ext import commands
from PIL import Image
from wordcloud import ImageColorGenerator, WordCloud

from cogs._config import MKSWT_KEY
from main import Bot

data = json.load(open("data/drama.json"))


def fillPhrase(phrase: str, data: dict):
    phr = phrase.split(" ")
    for i in range(len(phr)):
        for j in data["replacers"].keys():
            if phr[i].startswith(j):
                replacives = data[data["replacers"][j]]
                current_phrase = " ".join(phr)
                to_replace_with = random.choice(replacives)
                if to_replace_with not in current_phrase:
                    phr[i] = phr[i].replace(j, to_replace_with)
                    break
                else:
                    replacives.remove(to_replace_with)
                    phr[i] = phr[i].replace(j, random.choice(replacives))
                    break
    return " ".join(phr)


def getPhrase(data: dict):
    return random.choice(data["phrases"])


def generateRandomPhrase():
    return fillPhrase(getPhrase(data), data)


async def to_bytes(session: ClientSession, media_url: str):
    async with session.get(media_url) as response:
        response.raise_for_status()

        file_object = BytesIO(await response.read())

        try:
            image = Image.open(file_object)

            if image.format == "GIF":
                image.seek(0)
                image = image.convert("RGBA")
                image = image.convert("RGB")
                image = image.crop((0, 0, image.width, image.height))

            if image.mode == "RGBA":
                image = image.convert("RGB")

            aspect_ratio = image.width / image.height
            new_width = 512
            new_height = int(new_width / aspect_ratio)
            image = image.resize((new_width, new_height))

            output_file = BytesIO()
            image.save(output_file, format="PNG")

            return output_file.getvalue()
        except:
            return file_object.getvalue()


async def make_gif(
    bot: Bot,
    template: str,
    text: Optional[str],
    image: Optional[Attachment],
    swap: Optional[bool],
):
    url = f"https://api.makesweet.com/make/{template}"

    headers = {"Authorization": MKSWT_KEY}

    data = FormData()

    if text:
        url = url + f"?text={text}"

    if image:
        image_bytes = await to_bytes(bot.session, image.url)
        data.add_field(name="images", value=image_bytes, filename=image.filename)

    if text and swap:
        url = url + "&textfirst=1"

    async with bot.session.post(url, headers=headers, data=data) as response:
        if response.status == 200:
            r = await response.content.read()
            return BytesIO(r)
        else:
            bot.logger.error(f"Request failed with status {response.status}")
            return None


class Fun(commands.Cog):
    """Fun commands to spice things up!"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(name="drama", description="Generate funny piracy community drama.")
    async def drama(self, interaction: Interaction):
        phrase = generateRandomPhrase()
        return await interaction.response.send_message(content=phrase)

    @app_commands.command(name="create", description="Funny heart locket sealed away forever")
    @app_commands.describe(
        template="For example heart-locket for tasky my beloved",
        image="Will be prioritized to text if only one of them is available.",
        text="Will be passed as second parameter, i.e. right side of heart locked.",
        swap="Swap image and text so text comes first.",
    )
    @app_commands.choices(
        template=[
            Choice(name="Heart Locket", value="heart-locket"),
            Choice(name="Flying Bear", value="flying-bear"),
            Choice(name="Flag", value="flag"),
            Choice(name="Billboard City", value="billboard-cityscape"),
            Choice(name="Nesting Doll", value="nesting-doll"),
            Choice(name="Circuit Board", value="circuit-board"),
        ]
    )
    async def makesweet(
        self,
        interaction: Interaction,
        template: str,
        image: Optional[Attachment],
        text: Optional[str],
        swap: Optional[bool] = False,
    ):
        if not text and not image:
            return await interaction.response.send_message(
                f"{template} selected without either of `text` or `image`.", ephemeral=True
            )

        if image:
            file_extension = urllib.parse.urlparse(image.url).path.split(".")[-1]
            if file_extension not in ["jpeg", "jpg", "gif", "png", "webp"]:
                return await interaction.response.send_message(
                    "The only allowed formats are `jpg`, `png`, `gif` and `webp`!", ephemeral=True
                )

        await interaction.response.defer(thinking=True)
        gif = await make_gif(self.bot, template, text, image, swap)
        if gif is None:
            raise Exception("No gif was returned.")

        await interaction.followup.send(file=File(gif, f"{template}.gif"))

    @app_commands.checks.bot_has_permissions(attach_files=True, read_message_history=True)
    @app_commands.checks.cooldown(1, 300, key=None) # global cooldown
    @app_commands.command(name="wordcloud", description="Generate worcloud from channel's messages history.")
    @app_commands.guild_only()
    async def wordcloud(self, interaction: Interaction[Bot]):
        # This should be rare occurrence but since d.py says interaction.channel can be null sometimes
        # catch that here and early return if its ever null to avoid unnecessary processing or errors.
        if not interaction.channel:
            await interaction.response.send_message("No channel found to fetch messages.", ephemeral=True)
            return

        # how many number of messages to fetch from channel history
        max_limit = 20_000

        # sane defaults for wordcloud
        image_mode = "RGB"
        ## can be "clear" for transparent background
        ## change above to "RGBA" if below is set to "clear"
        image_bg_color = "black"
        max_words = 200
        ## list of words to filter out if any as required
        excluded = []
        ## you can pass a mask image object here
        ## something like numpy.array(Image.open(...))
        image_mask = None
        ## a coloring function compatible with wordcloud
        ## e.g. ImageColorGenerator(mask)
        coloring_func = None

        # keyword args to pass to WordCloud instance
        kwargs = {
            "mode": image_mode,
            "background_color": image_bg_color,
            "mask": image_mask,
            "color_func": coloring_func,
            "max_words": max_words,
            "stopwords": excluded or None,
            "width": 1920,
            "height": 1080,
        }

        await interaction.response.defer()
        buffer = StringIO()
        # Get messages history from current channel
        async for msg in interaction.channel.history(limit=max_limit):
            # should we filter out bots/webhooks here?
            # as well as non content like embeds/stickers/attachment only messages without content?
            buffer.write(msg.clean_content)
            buffer.write(" ")
        text = buffer.getvalue()
        buffer.close()
        # generation is sync/blocking function so loop in asyncio executor
        # to not block the bot's function while this is processing
        task = functools.partial(self._generate_wordcloud, text, **kwargs)
        loop = asyncio.get_running_loop()
        executor = loop.run_in_executor(None, task)
        # early exit if executor takes more than 2 minutes to process
        try:
            image = await asyncio.wait_for(executor, timeout=120)
        except asyncio.TimeoutError:
            await interaction.followup.send(
                "wordcloud generation took too long to generate funny image.",
                ephemeral=True, # make it non ephemeral if you want
            )
            return
        await interaction.followup.send(file=discord.File(image))
        # close resources to avoid mem leak
        image.close()
        return

    def _generate_wordcloud(self, text: str, **kwargs: Any) -> BytesIO:
        wc = WordCloud(**kwargs)
        wc.generate(text=text)
        buffer = BytesIO()
        buffer.name = "wordcloud.jpg" # change this to PNG format if image_mode is RGBA
        wc.to_file(buffer)
        buffer.seek(0)
        return buffer


async def setup(bot: Bot):
    await bot.add_cog(Fun(bot))
