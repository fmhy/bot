import re
import time
from datetime import datetime

import discord
from discord.ext import commands, tasks

from cogs._config import channel_ids, disallowed_channel_ids, managing_roles, url_regex, auto_thread_mappings
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

        self.all_disallowed_messages = []
        self.last_fetched_messages = {}

    @tasks.loop(minutes=5)
    async def update_single_page(self):
        async with self.bot.session.get(
            "https://raw.githubusercontent.com/fmhy/FMHYedit/main/single-page"
        ) as response:
            self.single_page = await response.text()
            self.bot.logger.info(f"Updated single page cache")

    @tasks.loop(minutes=15)
    async def update_disallowed_links(self):
        for channel_id in disallowed_channel_ids:
            channel = self.bot.get_channel(channel_id)
            if channel:
                messages = await self.fetch_new_messages(channel_id)
                self.bot.logger.info(f"Grabbing latest disallowed links from {channel_id}")
                for message in messages:
                    msg_links = set(
                        re.findall(
                            url_regex,
                            message.content,
                        )
                    )
                    self.all_disallowed_messages.extend(msg_links)

    async def fetch_new_messages(self, channel_id):
        channel = self.bot.get_channel(channel_id)
        last_fetched_message_id = self.last_fetched_messages.get(channel_id, None)

        messages = []
        async for msg in channel.history(limit=None, after=(discord.Object(last_fetched_message_id) if last_fetched_message_id else None)):
            messages.append(msg)

        self.last_fetched_messages[channel_id] = messages[-1].id if messages else last_fetched_message_id

        return messages

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
        self.update_disallowed_links.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        chan_id = str(message.channel.id)
        if chan_id in auto_thread_mappings and (
            auto_thread_mappings[chan_id] is None or auto_thread_mappings[chan_id] in message.content
        ):
            await message.create_thread(
                name="Auto-Thread - Please keep discussions in here!",
                reason="Auto thread created by FMHY Bot")

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

                # Check if any link is in disallowed channels
                # TODO: Add backreference to message containing link
                if any(link in self.all_disallowed_messages for link in message_links):
                    reply_message = await message.reply("**:warning: Warning: This link has been previously removed! Please check before submitting again. :warning:**")
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
