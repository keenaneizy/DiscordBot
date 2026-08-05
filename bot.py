"""
Phantom Picks Discord Bot — entry point.

Run with: python bot.py
Requires a .env file with DISCORD_TOKEN set (copy .env.example -> .env and
fill it in). See README.md for full setup + hosting instructions.
"""
import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import config

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("phantompicks")

# Privileged intents — both must also be enabled in the Discord Developer
# Portal under Bot -> Privileged Gateway Intents (see README.md step 3).
intents = discord.Intents.default()
intents.members = True           # required for on_member_join + role assignment
intents.message_content = True   # required to read "!" command text

bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents, help_command=None)

INITIAL_COGS = [
    "cogs.server_setup",
    "cogs.picks",
    "cogs.results",
    "cogs.moderation",
    "cogs.welcome",
    "cogs.help",
]


async def _provision_guild_safely(guild: discord.Guild):
    setup_cog = bot.get_cog("ServerSetup")
    if setup_cog is None:
        log.error("ServerSetup cog failed to load — skipping auto-provisioning.")
        return
    try:
        await setup_cog.provision_guild(guild)
    except discord.Forbidden:
        log.error(
            f"Missing permissions to provision '{guild.name}'. "
            "Make sure the bot's role has Manage Roles/Channels and is above "
            "Free Member / Phantom Pro in the role list."
        )
    except Exception:
        log.exception(f"Failed to provision guild {guild.name}")


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")

    for guild in bot.guilds:
        await _provision_guild_safely(guild)

    log.info("Phantom Picks is online and ready.")


@bot.event
async def on_guild_join(guild: discord.Guild):
    # Fires when the bot is invited to a server while already running —
    # on_ready only runs once per connection, so this is what provisions a
    # brand-new server without needing a manual restart or !setup.
    log.info(f"Joined new guild: {guild.name} ({guild.id})")
    await _provision_guild_safely(guild)


async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN not found. Copy .env.example to .env and fill in your bot token.")

    if os.getenv("RENDER_KEEP_ALIVE") == "1":
        from keep_alive import keep_alive
        keep_alive()

    async with bot:
        for ext in INITIAL_COGS:
            await bot.load_extension(ext)
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
