from __future__ import annotations

import logging
import traceback
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from main import Kannushi
    from utils.context import Context

logger = logging.getLogger(__name__)


class ErrorHandler(commands.Cog):
    def __init__(self, bot: Kannushi):
        self.bot: Kannushi = bot
        bot.on_error = self.on_error

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""
        await self.bot.wait_until_ready()
        if getattr(ctx, 'local_handled', False):  # Check if handled by local error handlers
            return

        ignored = (commands.CommandNotFound, commands.CommandOnCooldown, commands.NotOwner)  # Tuple of errors to ignore
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'Command `{ctx.command}` has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            return await ctx.author.send(f'The command `{ctx.command}` cannot be used in Private Messages.')

        elif isinstance(error, commands.BadArgument):
            return await ctx.send(f'Bad argument: {error}', ephemeral=True)

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                f'Missing required argument: `{error.param.name}` See {ctx.prefix}help {ctx.command} for more info',
                ephemeral=True)

        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send(
                f'I cannot complete this command, you are missing the following permission{"" if len(error.missing_permissions) == 1 else "s"}: {", ".join(error.missing_permissions)}')

        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send(
                f'I cannot complete this command, I am missing the following permission{"" if len(error.missing_permissions) == 1 else "s"}: {", ".join(error.missing_permissions)}')

        elif isinstance(error, commands.CheckFailure):
            return await ctx.send('Sorry, you cannot use this command')

        # Unhandled error, so just return the traceback
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        logger.error(tb)
        await ctx.send(f'An unexpected error has occurred! My owner has been notified.\n'
                       f'If you really want to know what went wrong:\n'
                       f'||```py\n{tb[-1][:150]}```||')

        e = discord.Embed(title=f'An unhandled error occurred in {ctx.guild} | #{ctx.channel}',
                          description=f'Invocation message: {ctx.message.content}\n'
                                      f'[Jump to message]({ctx.message.jump_url})',
                          color=discord.Color.red())
        e.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)

        await self.bot.owner.send(embed=e)
        fmt = "".join(tb)
        if len(fmt) >= 1980:
            paste, password = await self.bot.create_mb_paste(filename=f'traceback.py', content=fmt)
            await self.bot.owner.send(f'Traceback too long, uploaded to {paste.url} instead.\n'
                                      f'Password: `{password}` | Security token: `{paste.security_token}`')
        else:
            await self.bot.owner.send(f'```py\n{fmt}```')

    async def on_error(self, event, *args, **kwargs):
        await self.bot.wait_until_ready()
        msg = f'An error occurred in event `{event}`\nArgs: {args}\nKwargs: {kwargs}'
        logger.error(msg)
        await self.bot.owner.send(msg)
        tb = "".join(traceback.format_exc())
        logger.error(tb)
        if len(tb) >= 1980:
            paste, password = await self.bot.create_mb_paste(filename=f'traceback.py', content=tb)
            await self.bot.owner.send(f'Traceback too long, uploaded to {paste.url} instead.\n'
                                      f'Password: `{password}` | Security token: `{paste.security_token}`')
        else:
            await self.bot.owner.send(f'```py\n{tb}```')


async def setup(bot: Kannushi):
    await bot.add_cog(ErrorHandler(bot))


async def teardown(bot: Kannushi):
    bot.on_error = commands.Bot.on_error
