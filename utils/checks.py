from discord import app_commands
from discord.ext import commands

from utils.context import Context


async def check_permissions(ctx: Context, perms: dict[str, bool], *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    resolved = ctx.channel.permissions_for(ctx.author)
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def has_permissions(*, check=all, **perms: bool):
    async def pred(ctx: Context):
        return await check_permissions(ctx, perms, check=check)

    return commands.check(pred)


async def check_guild_permissions(ctx: Context, perms: dict[str, bool], *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def has_guild_permissions(*, check=all, **perms: bool):
    async def pred(ctx: Context):
        return await check_guild_permissions(ctx, perms, check=check)

    return commands.check(pred)

def hybrid_permissions_check(**perms: bool):
    async def pred(ctx: Context):
        return await check_guild_permissions(ctx, perms)

    def decorator(func):
        commands.check(pred)(func)
        app_commands.default_permissions(**perms)(func)
        return func

    return decorator
