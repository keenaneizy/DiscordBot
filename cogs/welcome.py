"""
Welcome cog — runs when a new member joins:
1. Auto-assigns the Free Member role.
2. Sends the Phantom Picks welcome DM (falls back gracefully if the member
   has server DMs disabled).
"""
import logging

import discord
from discord.ext import commands

import config
from formatting import build_welcome_dm

log = logging.getLogger("phantompicks.welcome")


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        free_role = discord.utils.get(member.guild.roles, name=config.ROLE_FREE)
        if free_role:
            try:
                await member.add_roles(free_role, reason="Phantom Picks: auto-assign base role on join")
            except discord.HTTPException:
                log.warning(f"Could not assign Free Member role to {member}")
        else:
            log.warning("Free Member role not found — run !setup to (re)create the server structure.")

        try:
            await member.send(build_welcome_dm())
        except discord.Forbidden:
            log.info(f"{member} has DMs disabled — could not send welcome DM")
        except discord.HTTPException:
            log.warning(f"Failed to DM welcome message to {member}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
