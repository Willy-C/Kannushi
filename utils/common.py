import copy
from typing import Optional

import discord
from discord.ext import commands

from utils.context import Context


def cleanup_code(content: str) -> str:
    """
    Automatically removes code blocks from the code.
    """
    if content.startswith('```'):
        split = content.split('\n')
        if ' ' not in split[0][3:].rstrip():  # Is language
            split = split[1:]
        else:
            split[0] = split[0][3:]  # Accidentally started coding on first line

        return '\n'.join(split).rstrip('` ')
    return content.strip('` \n')


async def copy_context(ctx: commands.Context, *,
                       author: Optional[discord.Member] = None,
                       channel: Optional[discord.TextChannel] = None,
                       **kwargs) -> Context:
    """
    Returns a new Context with changed message properties.
    """
    # copy the message and update the attributes
    alt_message: discord.Message = copy.copy(ctx.message)
    alt_message._update(kwargs)

    if author is not None:
        alt_message.author = author
    if channel is not None:
        alt_message.channel = channel

    # obtain and return a context of the same type
    return await ctx.bot.get_context(alt_message, cls=type(ctx))
