import discord
from discord.ext import commands

import cogs._helpers as hp


class Base64(commands.Cog):
    """Base64 commands"""

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def cog_before_invoke(self, ctx):
        """Triggers typing indicator on Discord before every command."""
        await ctx.trigger_typing()
        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot and not isinstance(message.webhook_id, int):
            return

        # Divolt commands
        if message.content == "/decode":
            actual_content = message.embeds[0].description.replace("**Reply to**: ", "")
            b64_decoded_strs = []
            for word in hp.words_from_content(actual_content):
                m = hp.b64decode(word)
                if m and len(m) > 8:
                    b64_decoded_strs.append(m)

            if len(b64_decoded_strs) == 0:
                await hp.send_message_to_divolt(message.channel.name, "No Base64 Found.")
            else:
                await hp.send_message_to_divolt(
                    message.channel.name,
                    "___Decoded Links___\n" + "> " + "\n\n> ".join(b64_decoded_strs),
                )

        if message.author.name == "___Base64Bot___":
            await message.delete()
            return

        for emb in message.embeds:
            if emb.author.name == "___Base64Bot___":
                await message.delete()

    # @commands.Cog.listener()
    # async def on_message(self,message:discord.Message):
    #     if not message.channel.id == 1099381748011380909:
    #         return
    #     if message.author.bot and not isinstance(message.webhook_id, int):
    #         return

    #     if message.author.bot: return
    #     b64_decoded_strs = []
    #     for word in hp.words_from_content(message.content):
    #         m = hp.b64decode(word)
    #         if m:
    #             b64_decoded_strs.append(m)

    #     if len(b64_decoded_strs) == 0:
    #         return

    #     b64_decoded_strs = b64_decoded_strs[:10]

    #     # sorry jsmsj :'(
    #     # oh its fine, im changing the code rn

    #     if len(b64_decoded_strs)>1:
    #         await message.add_reaction(hp.emoji_map[0])

    #     for i in range(1,len(b64_decoded_strs)+1):
    #         await message.add_reaction(hp.emoji_map[i])

    # @commands.Cog.listener()
    # async def on_raw_reaction_add(self,payload):
    #     user:discord.User = await self.bot.fetch_user(payload.user_id)
    #     if user.bot:return
    #     emoji = payload.emoji.name
    #     if emoji not in hp.emoji_map.values():
    #         return
    #     chan_id = payload.channel_id
    #     msg_id = payload.message_id
    #     channel = await self.bot.fetch_channel(chan_id)
    #     msg:discord.Message = await channel.fetch_message(msg_id)

    #     b64_decoded_strs = []
    #     for word in hp.words_from_content(msg.content):
    #         m = hp.b64decode(word)
    #         if m:
    #             b64_decoded_strs.append(m)
    #     b64_decoded_strs = b64_decoded_strs[:10]

    #     if len(b64_decoded_strs) == 0:
    #         return

    #     position = hp.emoji_num[emoji]

    #     if position == 0:
    #         emb = hp.cembed(title='Decoded Links',description='> ' + '\n\n> '.join(b64_decoded_strs))
    #         emb.add_field(name='Jump to Message',value=f'[Jump!]({msg.jump_url})')
    #         sent_msg = await user.send(embed=emb)
    #         await sent_msg.add_reaction('❌')
    #     else:
    #         emb = hp.cembed(title='Decoded Link',description=f'> {b64_decoded_strs[position-1]}')
    #         emb.add_field(name='Jump to Message',value=f'[Jump!]({msg.jump_url})')
    #         sent_msg = await user.send(embed=emb)
    #         await sent_msg.add_reaction('❌')

    # @commands.Cog.listener()
    # async def on_message_edit(self,before_message:discord.Message,message:discord.Message):
    #     # if not message.channel.id == 1099381748011380909:
    #     #     return

    #     if message.author.bot:
    #         return
    #     b64_decoded_strs = []
    #     for word in hp.words_from_content(message.content):
    #         m = hp.b64decode(word,from_msg=True)
    #         if m:
    #             b64_decoded_strs.append(m)

    #     if len(b64_decoded_strs) == 0:
    #         return
    #     b64_decoded_strs = b64_decoded_strs[:10]

    #     for emo in hp.emoji_map.values():
    #         await message.clear_reaction(emo)

    #     if len(b64_decoded_strs)>1:
    #         await message.add_reaction(hp.emoji_map[0])

    #     for i in range(1,len(b64_decoded_strs)+1):
    #         await message.add_reaction(hp.emoji_map[i])

    @commands.message_command(name="Decode base64")
    async def message_decode_b64(self, ctx: discord.ApplicationContext, message: discord.Message):
        b64_decoded_strs = []
        for word in hp.words_from_content(message.content):
            m = hp.b64decode(word)
            if m and len(m) > 8:
                b64_decoded_strs.append(m)

        if len(b64_decoded_strs) == 0:
            return await ctx.interaction.response.send_message("No Base64 Found.", ephemeral=True)

        emb = hp.cembed(title="Decoded Links", description="> " + "\n\n> ".join(b64_decoded_strs))

        await ctx.interaction.response.send_message(embed=emb, ephemeral=True)

    @commands.slash_command(name="encode", description="Encode to base64")
    async def encodeb64(self, ctx: discord.ApplicationContext, text: str):
        emb = hp.cembed("Encode to base64", str(hp.b64encode(text)))
        emb.set_footer(text=f"Encoded by {ctx.author.name}")
        await ctx.interaction.response.send_message(embed=emb, ephemeral=True)

    @commands.slash_command(name="decode", description="Decode from base64")
    async def decodeb64(self, ctx: discord.ApplicationContext, enocded_text: str):
        await ctx.interaction.response.send_message(str(hp.b64decode(enocded_text)), ephemeral=True)


def setup(bot):
    bot.add_cog(Base64(bot))
