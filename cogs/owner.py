from __future__ import annotations

import io
import textwrap
import traceback
import tabulate
from typing import Optional, Any, TYPE_CHECKING
from contextlib import redirect_stdout

import discord
from discord.ext import commands

from utils.common import cleanup_code, copy_context

if TYPE_CHECKING:
    from main import Kannushi
    from utils.context import Context


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot: Kannushi = bot
        self._last_result: Any = None

    @commands.command(name='eval')
    async def _eval(self, ctx: Context, *, code: str):
        """Evaluates python code in a single line or code block"""
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())
        code = cleanup_code(code)
        stdout = io.StringIO()
        to_compile = f'async def func():\n{textwrap.indent(code, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            await ctx.tick(True)
            if ret is None:
                if value:
                    content = f'```py\n{value}\n```'
                    await ctx.send(content, filetype='py')
            else:
                self._last_result = ret
                content = f'```py\n{value}{ret}\n```'
                await ctx.send(content, filetype='py')

    @commands.command(name='as')
    async def _sudo(self, ctx, channel: Optional[discord.TextChannel], target: discord.User, *, command: str):
        """
        Run a command as someone else.
        Try to resolve to a Member, if possible.
        """
        channel = channel or ctx.channel
        author = channel.guild.get_member(target.id) or target
        content = ctx.prefix + command
        new_ctx = await copy_context(ctx, author=author, channel=channel, content=content)
        if new_ctx.command is None:
            return await ctx.send(f'Command "{new_ctx.invoked_with}" is not found')

        await self.bot.invoke(new_ctx)

    @commands.command(name='load')
    async def load_cog(self, ctx: Context, *, cog: str):
        """Loads a Module.
        Accepts dot path. e.g: cogs.owner"""

        try:
            await self.bot.load_extension(cog)
        except Exception as e:

            await ctx.send(f'{await ctx.tick(False, reaction=False)} {type(e).__name__} - {e}')
        else:
            await ctx.send(f'{await ctx.tick(True, reaction=False)} loaded {cog}')

    @commands.command(name='unload')
    async def unload_cog(self, ctx, *, cog: str):
        """ Unloads a Module.
        Accepts dot path. e.g: cogs.owner"""

        try:
            await self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'{await ctx.tick(False, reaction=False)} {type(e).__name__} - {e}')
        else:
            await ctx.send(f'{await ctx.tick(True, reaction=False)} unloaded {cog}')

    @commands.command(name='reload')
    async def reload_cog(self, ctx, *, cog: str):
        """Reloads a Module.
        Accepts dot path e.g: cogs.owner"""
        try:
            try:
                await self.bot.reload_extension(cog)
            except commands.ExtensionNotLoaded:
                await self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'{await ctx.tick(False, reaction=False)} {type(e).__name__} - {e}')
        else:
            await ctx.send(f'{await ctx.tick(True, reaction=False)} reloaded {cog}')

    @commands.command(name="shutdown")
    async def logout(self, ctx):
        """
        Logs out the bot.
        """
        if not await ctx.confirm_prompt('Shutdown?'):
            return
        await ctx.message.add_reaction('\U0001f620')
        await ctx.bot.close()

    @commands.command(name='guilds')
    async def get_shared_guilds(self, ctx, user: discord.User):
        shared = []
        for guild in self.bot.guilds:
            if guild.get_member(user.id) is not None:
                shared.append(guild)
        fmt = "\n".join([f"{guild.name} - {guild.id}" for guild in shared])
        await ctx.send(f'```\nShared guilds with {user}\n{fmt}\n```')

    @commands.command(name='sql')
    async def run_query(self, ctx: Context, *, query):
        query = cleanup_code(query)

        is_multiple = query.count(';') > 1
        if is_multiple:
            # fetch does not support multiple statements
            method = self.bot.pool.execute
        else:
            method = self.bot.pool.fetch

        try:
            results = await method(query)
        except Exception:
            return await ctx.send(f'```py\n{traceback.format_exc()}\n```')

        rows = len(results)
        if is_multiple or rows == 0:
            return await ctx.send(f'```\n{results}```')
        headers = list(results[0].keys())
        values = [list(map(repr, v)) for v in results]
        table = tabulate.tabulate(values, tablefmt='psql', headers=headers)
        if len(table) > 1000:
            await ctx.send(table, force_upload=True)
        else:
            await ctx.send(f'```\n{table}```')


async def setup(bot: Kannushi):
    await bot.add_cog(Owner(bot))
