from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from main import Kannushi
    from utils.context import Context


class Mod(commands.Cog):
    def __init__(self, bot: Kannushi):
        self.bot: Kannushi = bot

    async def _sad_clean(self, ctx: Context, search: int): # No manage message permission, only delete bot's message
        count = 0
        async for msg in ctx.history(limit=search, before=ctx.message):
            if msg.author == ctx.me and not (msg.mentions or msg.role_mentions):
                await msg.delete()
                count += 1
        return {str(self.bot.user): count}

    async def _good_clean(self, ctx: Context, search: int): # Do have permission, so delete any invocation messages as well
        prefixes = tuple(await self.bot.get_prefix(ctx.message))
        def check(m):
            return m.author == ctx.me or m.content.startswith(prefixes)
        deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
        return Counter(msg.author.display_name for msg in deleted)

    async def _non_mod_user_clean(self, ctx: Context, search: int):
        prefixes = tuple(await self.bot.get_prefix(ctx.message))
        def check(m):
            return (m.author == ctx.me or m.content.startswith(prefixes)) and not (m.mentions or m.role_mentions)

        deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
        return Counter(msg.author.display_name for msg in deleted)

    @commands.command()
    async def clean(self, ctx: Context, search: int = 25):
        """Cleans up the bot's messages from the channel.

        If a search number is specified, it searches that many messages to delete.
        If the bot has Manage Messages permissions then it will try to delete
        messages that look like they invoked the bot as well.

        After the cleanup is completed, the bot will send you a message with
        which people got their messages deleted and their count. This is useful
        to see which users are spammers.

        Members with Manage Messages can search up to 1000 messages.
        Members without can search up to 25 messages.
        """
        clean_method = self._sad_clean
        is_mod = ctx.channel.permissions_for(ctx.author).manage_messages
        if ctx.channel.permissions_for(ctx.me).manage_messages:
            if is_mod:
                clean_method = self._good_clean
            else:
                clean_method = self._non_mod_user_clean

        if is_mod:
            search = min(max(2, search), 1000)
        else:
            search = min(max(2, search), 25)

        spam = await clean_method(ctx, search)
        deleted = sum(spam.values())

        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed']
        if deleted:
            messages.append('')
            spammers = sorted(spam.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'- **{author}**: {count}' for author, count in spammers)

        await ctx.send('\n'.join(messages), delete_after=10)
        await ctx.tick(True)


async def setup(bot: Kannushi):
    await bot.add_cog(Mod(bot))
