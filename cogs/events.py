import re
import time
from datetime import datetime

import discord
from discord.ext import commands, tasks

from cogs._config import (
    auto_thread_mappings,
    channel_ids,
    disallowed_channel_ids,
    managing_roles,
    url_regex,
)
from cogs._helpers import cembed
from main import Bot


class EventHandling(commands.Cog):
    """EventHandling commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.bookmark_emoji = discord.PartialEmoji(name="🔖")
        self.del_emoji = discord.PartialEmoji(name="❌")
        self.list_emoji = discord.PartialEmoji(name="📋")
        self.last_single_page_update = 0
        self.single_page = ""

        self.all_disallowed_messages = set()
        self.last_fetched_messages = {}

    @tasks.loop(minutes=5)
    async def update_single_page(self):
        async with self.bot.session.get(
            "https://raw.githubusercontent.com/fmhy/FMHYedit/main/single-page"
        ) as response:
            self.single_page = await response.text()
            self.bot.logger.info("Updated single page cache")
            self.last_single_page_update = time.time()

    @tasks.loop(minutes=15)
    async def update_disallowed_links(self):
        for channel_id in disallowed_channel_ids:
            channel = self.bot.get_channel(channel_id)
            if channel:
                messages = await self.fetch_new_messages(channel_id)
                total_links_added = 0
                for message in messages:
                    msg_links = set(
                        re.findall(
                            url_regex,
                            message.content,
                        )
                    )
                    for link in msg_links:
                        self.all_disallowed_messages.add((link, message.jump_url))
                    total_links_added += len(msg_links)

                if total_links_added > 0:
                    self.bot.logger.info(f"Added {total_links_added} links from {channel_id}")


    async def fetch_new_messages(self, channel_id):
        channel = self.bot.get_channel(channel_id)
        last_fetched_message_id = self.last_fetched_messages.get(channel_id, None)

        messages = []
        async for msg in channel.history(
            limit=None,
            after=(discord.Object(last_fetched_message_id) if last_fetched_message_id else None),
        ):
            messages.append(msg)

        self.last_fetched_messages[channel_id] = (
            messages[-1].id if messages else last_fetched_message_id
        )

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

    async def filter_nonduplicates_embed(self, message):
        message_links = set(re.findall(url_regex, message.content))
        if message_links:
            (
                duplicate_links,
                non_duplicate_links,
            ) = await self.get_duplicate_non_duplicate_links(message_links)

            non_duplicate_links_string = "\n".join(
                [f"{protocol}://{link}" for protocol, link in non_duplicate_links]
            )
            non_duplicate_links_embed = cembed(
                title="__Non-Duplicate Links:__",
                description=f"{non_duplicate_links_string}",
            )
            non_duplicate_links_embed.set_author(
                name=message.author.name,
                icon_url=message.author.display_avatar,
            )

            return non_duplicate_links_embed

    @commands.Cog.listener()
    async def on_ready(self):
        self.update_single_page.start()
        self.update_disallowed_links.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        chan_id = str(message.channel.id)
        if chan_id in auto_thread_mappings and (
            auto_thread_mappings[chan_id] is None
            or auto_thread_mappings[chan_id] in message.content
        ):
            await message.create_thread(
                name="Auto-Thread - Please keep discussions in here!",
                reason="Auto thread created by FMHY Bot",
            )

        if message.author.bot:
            return
        if message.channel.id in channel_ids:
            message_links = set(re.findall(url_regex, message.content))
            if message_links:
                (
                    duplicate_links,
                    non_duplicate_links,
                ) = await self.get_duplicate_non_duplicate_links(message_links)
                embed = discord.Embed(
                    title=":warning: Warning",
                    description="",
                    color=discord.Color.orange()
                )

                # One link, duplicate
                if len(message_links) == 1 and len(duplicate_links) == 1:
                    embed.description = "**This link is already in the wiki!**"
                # All links, duplicates
                elif len(message_links) > 1 and len(message_links) == len(duplicate_links):
                    embed.description = "**All of these links are already in the wiki!**"
                # Partial duplicates
                elif len(message_links) > 1 and len(duplicate_links) >= 1:
                    duplicate_links_string = "\n".join(
                        [f"{protocol}://{link}" for protocol, link in duplicate_links]
                    )
                    embed.add_field(name="Duplicate Link", value=duplicate_links_string, inline=False)

                    embed.set_footer(text="React with 📋 for a list of your non-duplicated links")

                # Disallowed links
                for link in message_links:
                    duplicate_links_string = "\n".join(
                        [f"{'://'.join(disallowed_link)} | [Go to message]({jump_url})" for disallowed_link, jump_url in self.all_disallowed_messages if link == disallowed_link]
                    )
                    if len(duplicate_links_string) > 0:
                        embed.add_field(name="Previously Removed", value=duplicate_links_string, inline=False)

                if len(embed.fields) > 0 or len(embed.description) > 0:
                    reply_message = await message.reply(embed=embed)
                    await reply_message.add_reaction("❌")
                    
                    if len(embed.footer) > 0:
                        await reply_message.add_reaction("📋")
                
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
                embed.set_author(name=msg.author.name, icon_url=msg.author.display_avatar)
                embed.description = msg.content[:4096]
                embed.add_field(name="Jump", value=f"[Go to Message!]({msg.jump_url})")
                embed.set_footer(text=f"Guild: {channel.guild.name} | Channel: #{channel.name}")
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

            # Send non-duplicate links as embed
            if (
                emoji == self.list_emoji
                and msg.author.id == self.bot.user.id
                and payload.user_id != self.bot.user.id
            ):
                if msg.reference is not None and not isinstance(
                    msg.reference.resolved, discord.DeletedReferencedMessage
                ):
                    original_message = msg.reference.resolved
                    non_duplicate_links_embed = await self.filter_nonduplicates_embed(original_message)

                    if non_duplicate_links_embed is not None:
                        await msg.reply(embed=non_duplicate_links_embed)
                else:
                    await msg.reply("Unable to find original message")
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
