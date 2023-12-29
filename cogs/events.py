import re
import time
from datetime import datetime

import discord
from discord.ext import commands, tasks

from cogs._config import channel_ids, managing_roles, url_regex, auto_thread_channels, auto_thread_roles
from cogs._helpers import cembed
from main import Bot


class EventHandling(commands.Cog):
    """EventHandling commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.bookmark_emoji = discord.PartialEmoji(name="🔖")
        self.del_emoji = discord.PartialEmoji(name="❌")
        self.last_single_page_update = 0
        self.single_page = ""
        self.dead_sites_messages = set()
        self.deleted_sites_messages = set()

    @tasks.loop(minutes=5)
    async def update_single_page(self):
        async with self.bot.session.get(
            "https://raw.githubusercontent.com/fmhy/FMHYedit/main/single-page"
        ) as response:
            self.single_page = await response.text()

    async def cog_before_invoke(self, ctx):
        """Triggers typing indicator on Discord before every command."""
        await ctx.channel.typing()
        return

    async def get_duplicate_non_duplicate_links(self, message_links):
        if time.time() - self.last_single_page_update >= 300:
            await self.update_single_page()

        wiki_links = set(
            re.findall(
                url_regex,
                self.single_page,
            )
        )
        duplicate_links = wiki_links.intersection(message_links)
        non_duplicate_links = message_links - duplicate_links

        return duplicate_links, non_duplicate_links

    @commands.Cog.listener()
    async def on_ready(self):
        self.update_single_page.start()

        dead_sites_channel = self.bot.get_channel(988133247575810059)
        if dead_sites_channel:
            self.dead_sites_messages = set(await dead_sites_channel.history(limit=None).flatten())

        deleted_sites_channel = self.bot.get_channel(986617857133649921)
        if deleted_sites_channel:
            self.deleted_sites_messages = set(
                await deleted_sites_channel.history(limit=None).flatten()
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id in auto_thread_channels and any(
            str(role) in message.content for role in auto_thread_roles
        ):
            await message.create_thread(
                name="Auto-Thread - Please keep discussions in here!",
                reason="Auto thread created by FMHY Bot",
                auto_archive_duration=60)

        if message.author.bot:
            return
        if message.channel.id in channel_ids:
            message_links = set(re.findall(url_regex, message.content))
            if message_links:
                (
                    duplicate_links,
                    non_duplicate_links,
                ) = await self.get_duplicate_non_duplicate_links(message_links)

                # One link, duplicate
                if len(message_links) == 1 and len(duplicate_links) == 1:
                    reply_message = await message.reply("**This link is already in the wiki!**")
                    await reply_message.add_reaction("❌")
                    return
                # All links, duplicates
                elif len(message_links) > 1 and len(message_links) == len(duplicate_links):
                    reply_message = await message.reply(
                        "**All of these links are already in the wiki!**"
                    )
                    await reply_message.add_reaction("❌")
                    return
                # Partial duplicates
                elif len(message_links) > 1 and len(duplicate_links) >= 1:
                    non_duplicate_links_string = "\n".join(
                        [f"{protocol}://{link}" for protocol,
                            link in non_duplicate_links]
                    )
                    non_duplicate_links_embed = cembed(
                        title="__Non-Duplicate Links:__",
                        description=f"{non_duplicate_links_string}",
                    )
                    non_duplicate_links_embed.set_author(
                        name=message.author.name,
                        icon_url=message.author.display_avatar,
                    )

                    reply_message = await message.reply(embed=non_duplicate_links_embed)
                    await reply_message.add_reaction("❌")
                    return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        emoji = payload.emoji
        chan_id = payload.channel_id
        msg_id = payload.message_id
        channel = await self.bot.fetch_channel(chan_id)
        msg: discord.Message = await channel.fetch_message(msg_id)
        user = await self.bot.fetch_user(payload.user_id)
        if not isinstance(channel, discord.DMChannel):
            # Bookmark message
            if emoji == self.bookmark_emoji:
                attachments = msg.attachments
                embed = discord.Embed(color=0x2B2D31, timestamp=datetime.now())
                embed.set_author(name=msg.author.name,
                                 icon_url=msg.author.display_avatar)
                embed.description = msg.content[:4096]
                embed.add_field(
                    name="Jump", value=f"[Go to Message!]({msg.jump_url})")
                embed.set_footer(
                    text=f"Guild: {channel.guild.name} | Channel: #{channel.name}")
                attach = ""
                if attachments:
                    img_added = False
                    for attachment in attachments:
                        if img_added is False:
                            if attachment.content_type in [
                                "image/avif",
                                "image/jpeg",
                                "image/png",
                            ]:
                                try:
                                    embed.set_image(url=attachment.url)
                                except:
                                    pass
                                img_added = True

                        attach += f"{attachment.url}\n"

                try:
                    sent = await user.send(content=f"\n{attach}", embed=embed)
                    await sent.add_reaction("❌")
                except discord.Forbidden:
                    await channel.send(
                        f"**{user.mention} I do not have permission to DM you. Please enable DMs for this server.**"
                    )

            # Delete message if user has roles that can manage messages
            if (
                emoji == self.del_emoji
                and msg.author.id == self.bot.user.id
                and payload.user_id != self.bot.user.id
            ):
                for role in payload.member.roles:
                    if role.id in managing_roles:
                        if msg.reference is not None and not isinstance(
                            msg.reference.resolved, discord.DeletedReferencedMessage
                        ):
                            await msg.reference.resolved.delete()
                        await msg.delete()
                        break
        else:
            # Delete message
            if (
                emoji == self.del_emoji
                and msg.author.id == self.bot.user.id
                and payload.user_id != self.bot.user.id
            ):
                await msg.delete()


async def setup(bot: Bot):
    await bot.add_cog(EventHandling(bot))
