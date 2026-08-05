"""
Shared permission check for admin-only commands.

"Only I can post here" channels are enforced two ways:
1. Discord channel permission overwrites deny @everyone / Free Member /
   Phantom Pro send access (set up in cogs/server_setup.py).
2. This command-level check, so admin-only commands refuse to run for
   anyone else even if channel permissions are ever changed, or the
   command is invoked in some other channel.
"""
import os

from discord.ext import commands

import config


async def _predicate(ctx: commands.Context) -> bool:
    if ctx.guild is None:
        return False
    if ctx.author.guild_permissions.administrator:
        return True
    if ctx.author.id == ctx.guild.owner_id:
        return True
    extra_owner_id = config.BOT_OWNER_ID or os.getenv("BOT_OWNER_ID")
    if extra_owner_id and str(ctx.author.id) == str(extra_owner_id):
        return True
    return False


def is_admin_or_owner():
    """Command check: passes for server admins, the server owner, or the
    optional BOT_OWNER_ID override in .env."""
    return commands.check(_predicate)
