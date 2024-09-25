from datetime import UTC, datetime

import discord
from discord.ext import commands


class HelpMenu(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(description=page, color=discord.Color.blue())
            embed.set_footer(
                text="Use help [command] or help [category] | <> is required | [] is optional"
            )
            embed.timestamp = datetime.now(UTC)
            await destination.send(embed=embed)
