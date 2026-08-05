"""
Moderation cog

- #member-wins: bot reacts with 👻 on every message posted there.
- #free-chat: lightweight spam auto-moderation — message-rate flooding and
  repeated/duplicate message spam. This is intentionally simple (in-memory,
  not persisted); it's meant to keep free-chat readable, not to be a full
  auto-mod system.
"""
import collections
import time

import discord
from discord.ext import commands

import config

RATE_LIMIT_WINDOW_SECONDS = 6
RATE_LIMIT_MAX_MESSAGES = 5
DUPLICATE_THRESHOLD = 3
WARN_COOLDOWN_SECONDS = 30


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # user_id -> deque of (timestamp, content) for their last few messages
        self._recent_messages = collections.defaultdict(lambda: collections.deque(maxlen=10))
        self._last_warned = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None or message.channel.name is None:
            return

        if message.channel.name == config.CH_MEMBER_WINS:
            try:
                await message.add_reaction("👻")
            except discord.HTTPException:
                pass
            return

        if message.channel.name == config.CH_FREE_CHAT:
            await self._check_spam(message)

    async def _check_spam(self, message: discord.Message):
        now = time.time()
        history = self._recent_messages[message.author.id]
        history.append((now, message.content))

        recent = [(t, c) for t, c in history if now - t <= RATE_LIMIT_WINDOW_SECONDS]
        recent_contents = [c for _, c in recent]

        is_flooding = len(recent) >= RATE_LIMIT_MAX_MESSAGES
        is_duplicate_spam = (
            len(recent_contents) >= DUPLICATE_THRESHOLD
            and len(set(recent_contents[-DUPLICATE_THRESHOLD:])) == 1
            and recent_contents[-1].strip() != ""
        )

        if not (is_flooding or is_duplicate_spam):
            return

        try:
            await message.delete()
        except discord.HTTPException:
            pass

        last_warn = self._last_warned.get(message.author.id, 0)
        if now - last_warn > WARN_COOLDOWN_SECONDS:
            self._last_warned[message.author.id] = now
            try:
                warning = await message.channel.send(
                    f"⚠️ {message.author.mention} slow down — that looked like spam. Keep it chill in here 👻"
                )
                await warning.delete(delay=8)
            except discord.HTTPException:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
