import asyncio
import re
import time
from datetime import datetime

import discord
from discord.ext import commands, tasks

from bot.core import Bot
from bot.core.config import (
    auto_thread_mappings,
    channel_ids,
    disallowed_channel_ids,
    managing_roles,
    url_regex,
)
from bot.core.helpers import cembed


class Events(commands.Cog):
    """Event handler cog, for bookmarks, etc."""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.emojis = {
            "bookmark": discord.PartialEmoji(name="🔖"),
            "del": discord.PartialEmoji(name="❌"),
            "list": discord.PartialEmoji(name="📋"),
            "raised_hand": discord.PartialEmoji(name="✋"),
        }
        self.single_page_cache = None

        self.last_fetched_messages = {}
        self.first_run = True

    async def cog_load(self) -> None:
        self.update_single_page.start()
        self.update_disallowed_links.start()
        return await super().cog_load()

    async def cog_unload(self) -> None:
        self.update_single_page.stop()
        self.update_disallowed_links.stop()
        return await super().cog_unload()

    @tasks.loop(minutes=5)
    async def update_single_page(self):
        headers = {}
        if self.single_page_cache:
            headers['If-None-Match'] = self.single_page_cache.get('ETag', '')

        async with self.bot.session.get("https://api.fmhy.net/single-page", headers=headers) as response:
            if response.status == 200:
                response_text = await response.text()
                wiki_links = await self.process_links(response_text)
                self.single_page_cache = {
                    'wiki_links': wiki_links,
                    'ETag': response.headers.get('ETag', '')
                }
                self.bot.logger.info("Updated single page cache")
            elif response.status != 304:
                self.bot.logger.warning(f"Error fetching single page: {response.status}")

    @tasks.loop(minutes=10)
    async def update_disallowed_links(self):
        tasks = []
        for channel_id in disallowed_channel_ids:
            if channel := self.bot.get_channel(channel_id):
                tasks.append(self.process_channel(channel))

        await asyncio.gather(*tasks)

        if self.first_run:
            self.bot.logger.info("Checking for messages potentially missed")
            for channel_id in channel_ids:
                if not (channel := self.bot.get_channel(channel_id)):
                    continue
                if not isinstance(channel, discord.TextChannel):
                    continue

                messages = await self.fetch_messages_without_bot_replies(channel)
                for message in messages:
                    await self.check_message_for_links(message)
            self.first_run = False

    async def process_channel(self, channel):
        messages = await self.fetch_new_messages(channel)

        links_added = 0
        for message in messages:
            # Grab message content and, if exists, content of forwarded message.
            content = message.content
            if (
                message.reference is not None
                and message.reference.type is discord.MessageReferenceType.forward
            ):
                for snapshot in message.message_snapshots:
                    content = content + snapshot.content
            if not content:
                continue

            # Some context-important messages may contain links that should be ignored.
            if any(reaction.emoji == self.emojis["raised_hand"] for reaction in message.reactions):
                continue

            if matches := await self.process_links(content):
                filtered = [
                    (protocol, domain) for protocol, domain in matches
                    if "/channels/" not in domain
                    or "discord.com" not in domain
                ]

                links_added += len(filtered)
                self.bot.all_disallowed_messages.update((link, f"{channel.id}/{message.id}") for link in filtered)

        if links_added > 0:
            self.bot.logger.info(f"Added {links_added} links from #{channel.name}")

    @update_disallowed_links.before_loop
    async def update_disallowed_links_before_loop(self):
        await self.bot.wait_until_ready()

    async def process_links(self, content):
        return {(m.group(1), m.group(2).lower()) for m in url_regex.finditer(content)}

    async def fetch_new_messages(self, channel):
        last_fetched_message_id = self.last_fetched_messages.get(channel.id)

        messages = []
        fetch_limit = 200

        while True:
            batch = [msg async for msg in channel.history(
                limit=fetch_limit,
                after=(
                    discord.Object(last_fetched_message_id) if last_fetched_message_id else None
                ),
                oldest_first=True,
            )]

            if not batch:
                break

            messages.extend(batch)
            last_fetched_message_id = batch[-1].id
            fetch_limit = 1000

        if messages:
            self.last_fetched_messages[channel.id] = (
                messages[-1].id if messages else last_fetched_message_id
            )

        return messages

    async def fetch_messages_without_bot_replies(self, channel):
        messages = []
        fetched_messages = [msg async for msg in channel.history(limit=25)]

        messages_with_bot_replies = set(msg.reference.message_id for msg in fetched_messages if msg.reference and msg.author == self.bot.user)

        messages.extend(msg for msg in fetched_messages if msg.id not in messages_with_bot_replies and not msg.author.bot)

        return messages

    async def check_message_for_links(self, message):
        if not message.content:
            return

        if message_links := await self.process_links(message.content):
            duplicate_links, non_duplicate_links = await self.get_duplicate_non_duplicate_links(message_links)

            embed = discord.Embed(
                title=":warning: Warning",
                description="",
                color=discord.Color.orange()
            )

            # Handle duplicate cases
            if len(message_links) == 1 and len(duplicate_links) == 1:
                embed.description = "**This link is already in the wiki!**"
            elif len(message_links) > 1 and len(message_links) == len(duplicate_links):
                embed.description = "**All of these links are already in the wiki!**"
            elif len(message_links) > 1 and len(duplicate_links) >= 1:
                dup_string = "\n".join(f"{p}://{d}" for p, d in duplicate_links)
                chunks = self.chunk_string(dup_string)

                for i, chunk in enumerate(chunks):
                    name = "Duplicate Link" if i == 0 else "Duplicate Link (cont.)"
                    embed.add_field(name=name, value=chunk, inline=False)

                if non_duplicate_links:
                    embed.set_footer(text="React with 📋 for a list of your non-duplicated links")

            # Disallowed links
            disallowed_entries = []
            for link in message_links:
                matches = {entry for entry in self.bot.all_disallowed_messages if entry[0] == link}

                for match in matches:
                    disallowed_entries.append((link, match[1]))

            if disallowed_entries:
                self.bot.logger.info(disallowed_entries)

                disallowed_text = "\n".join(
                    f"{p}://{d} | [Context](https://discord.com/channels/{message.guild.id}/{jump_ref})"
                    for (p, d), jump_ref in disallowed_entries
                )
                chunks = self.chunk_string(disallowed_text)

                for i, chunk in enumerate(chunks):
                    name = "🚫 Previously Removed Links" if i == 0 else "🚫 Previously Removed Links (cont.)"
                    embed.add_field(name=name, value=chunk, inline=False)

            if len(embed.fields) > 0 or len(embed.description) > 0:
                reply_message = await message.reply(embed=embed)
                await reply_message.add_reaction("❌")

                if non_duplicate_links and duplicate_links:
                    await reply_message.add_reaction("📋")

    async def get_duplicate_non_duplicate_links(self, message_links):
        if self.single_page_cache and self.single_page_cache.get('wiki_links'):
            wiki_links = self.single_page_cache['wiki_links']

            duplicate_links = wiki_links.intersection(message_links)
            non_duplicate_links = message_links - duplicate_links

            return duplicate_links, non_duplicate_links
        else:
            return set(), message_links

    async def filter_nonduplicates_embed(self, message):
        if message_links := await self.process_links(message.content):
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

    def chunk_string(self, input_str, max_length=1024):
        chunks = []
        while len(input_str) > max_length:
            split_point = input_str.rfind('\n', 0, max_length)
            if split_point == -1:
                split_point = max_length  # No newline found, hard cut
            chunks.append(input_str[:split_point])
            input_str = input_str[split_point:].lstrip()
        if input_str:
            chunks.append(input_str)
        return chunks

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if thread.parent_id in channel_ids:
            message = await thread.fetch_message(thread.id)
            await self.check_message_for_links(message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        chan_id = str(message.channel.id)
        if chan_id in auto_thread_mappings and (
            auto_thread_mappings[chan_id] is None
            or auto_thread_mappings[chan_id] in message.content
        ):
            await message.create_thread(
                name="🧵 Please keep discussions in here!",
                reason="Auto thread created by FMHY Bot",
            )
            return

        if message.author.bot:
            return
        if (
            (
                message.channel.id in channel_ids or 
                (isinstance(message.channel, discord.Thread) and message.channel.parent_id in channel_ids)
            )
            and not isinstance(message.channel, discord.ForumChannel)
        ):
            await self.check_message_for_links(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        emoji = payload.emoji

        if emoji not in self.emojis.values():
            return

        channel = await self.bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)

        referenced_msg = msg.reference.resolved if msg.reference else None

        # Send non-duplicate links as embed
        if (
            emoji == self.emojis["list"]
            and msg.author.id == self.bot.user.id
            and payload.user_id != self.bot.user.id
            and referenced_msg
        ):
            if not isinstance(referenced_msg, discord.DeletedReferencedMessage):
                if embed := await self.filter_nonduplicates_embed(referenced_msg):
                    await msg.reply(embed=embed)
            else:
                await msg.reply("Unable to find original message")

            await msg.clear_reaction(self.emojis["list"])
            return

        # Bookmark message
        if (
            emoji == self.emojis["bookmark"]
            and not isinstance(channel, discord.DMChannel)
        ):
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
                sent = await payload.member.send(content=f"\n{attach}", embed=embed)
                await sent.add_reaction(self.emojis["del"])
            except discord.Forbidden:
                # Nobody cares about this
                pass

            return

        # Delete message if user (is author of original message OR has roles that can manage messages)
        if (
            emoji == self.emojis["del"]
            and msg.author.id == self.bot.user.id
            and payload.user_id != self.bot.user.id
        ):
            if not isinstance(channel, discord.DMChannel):
                managing_user = any(role.id in managing_roles for role in payload.member.roles)
                is_author = msg.author.id == payload.user_id

                if managing_user or is_author:
                    await msg.delete()

                    if not isinstance(referenced_msg, discord.DeletedReferencedMessage):
                        await referenced_msg.delete()
            else:
                await msg.delete()
            return

        # Remove link from all_disallowed_messages if new raised hand reaction
        if (
            emoji == self.emojis["raised_hand"]
            and msg.author.id != self.bot.user.id
        ):
            if not isinstance(channel, discord.DMChannel):
                message_links = await self.process_links(msg.content)
                for link in message_links:
                    self.bot.all_disallowed_messages.discard((link, f"{channel.id}/{msg.id}"))
                    # fix this - doesn't know which channel link was originally posted in
            return

async def setup(bot: Bot):
    await bot.add_cog(Events(bot))
