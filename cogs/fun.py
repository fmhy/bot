import urllib.parse
from io import BytesIO
from typing import Optional

from aiohttp import FormData
from aiohttp.client import ClientSession
from discord import Attachment, File, Interaction, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from PIL import Image

from cogs._config import MKSWT_KEY
from core import drama
from main import Bot


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
        phrase = drama.generateRandomPhrase()
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


async def setup(bot: Bot):
    await bot.add_cog(Fun(bot))
