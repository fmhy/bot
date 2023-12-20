import random
import re

import discord
from discord.ext import commands

from cogs._config import url_regex
from cogs._search_help import execute
from main import Bot


class WikiCommands(commands.Cog):
    """WikiCommands commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def get_urls_from_rentry(self):
        async with self.bot.session.get("https://rentry.co/oghty/raw") as response:
            urls = await response.text()
        return list(
            set([f"{protocol}://{domain}" for protocol, domain in re.findall(url_regex, urls)])
        )

    async def cog_before_invoke(self, ctx):
        """Triggers typing indicator on Discord before every command."""
        await ctx.channel.typing()
        return

    @commands.slash_command(
        name="list", description="Displays random URL(s) from the list of lists."
    )
    async def list_links(self, ctx: discord.ApplicationContext, url_num: int):
        # await ctx.defer()
        if url_num < 1:
            url_num = 1
        elif url_num > 25:
            url_num = 25
        list_urls = await self.get_urls_from_rentry()
        random_urls = random.sample(list_urls, url_num)
        title = f"Here are {url_num} random URL{'s' if url_num > 1 else ''} from the list of lists:"
        list_embed = discord.Embed(
            title=title,
            color=0x2B2D31,
        )
        list_embed.set_footer(text="Source: https://rentry.co/oghty")
        list_embed.description = "\n".join([f"{url}" for url in random_urls])
        # await ctx.interaction.followup.send()
        await ctx.interaction.response.send_message(embed=list_embed, ephemeral=True)

    @commands.slash_command(name="search", description="Search for query in the wiki")
    async def searchwiki(self, ctx: discord.ApplicationContext, query: str):
        search = await execute(query)
        results = search[0]
        list_embed = discord.Embed(title=f"Search Results for {query}", color=0x2B2D31)
        list_embed.description = "\n\n".join(results)
        await ctx.respond(embed=list_embed, ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(WikiCommands(bot))
