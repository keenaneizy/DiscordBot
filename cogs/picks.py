"""
Picks cog — !freepick and !vippick.

Both commands take quoted arguments for anything that can contain spaces
(sport names like "College Football", team names). See !help (cogs/help.py)
or README.md for exact syntax and examples.

Posting: rather than a detailed one-message-per-pick post, each pick gets
appended as one line ("Team ML 1u") to that channel's single running
"today's picks" message — see rollup.py. kalshi_price is still required and
stored on the pending pick, since !result's `auto` amount needs it to
calculate P&L/units — model probability and edge aren't collected at all
since nothing displays or uses them anymore.
"""
import discord
from discord.ext import commands

import config
from checks import is_admin_or_owner
from data_store import DataStore
from formatting import build_pick_line
from rollup import append_line, resync
from sports import resolve_sport


class Picks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store = DataStore()

    @staticmethod
    def _find_channel(guild: discord.Guild, name: str) -> discord.TextChannel | None:
        return discord.utils.get(guild.text_channels, name=name)

    @staticmethod
    async def _cleanup_invocation(ctx: commands.Context):
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

    # ── !freepick ────────────────────────────────────────────────────────
    @commands.command(name="freepick")
    @is_admin_or_owner()
    @commands.guild_only()
    async def freepick(self, ctx: commands.Context, sport: str, away_team: str, home_team: str,
                        picked_team: str, kalshi_price: float):
        sport_code = resolve_sport(sport)
        if sport_code is None:
            await ctx.send(f"⚠️ Unknown sport `{sport}`. Use MLB, NFL, NBA, \"College Football\", or \"College Basketball\".")
            return

        if not (0 < kalshi_price < 100):
            await ctx.send("⚠️ Kalshi price must be between 1 and 99 (cents).")
            return

        channel = self._find_channel(ctx.guild, config.CH_FREE_PICKS)
        if channel is None:
            await ctx.send(f"⚠️ Couldn't find #{config.CH_FREE_PICKS}. Run `!setup` first.")
            return

        data = self.store.load()
        await append_line(channel, data["daily_picks"]["free"], "FREE PICKS", build_pick_line(picked_team))
        data["pending_picks"].append({
            "sport": sport_code, "away": away_team, "home": home_team,
            "picked": picked_team, "type": "free", "price": kalshi_price,
        })
        self.store.save(data)

        await self._cleanup_invocation(ctx)
        if channel.id != ctx.channel.id:
            await ctx.send(f"✅ Free pick posted in {channel.mention}.", delete_after=5)

    # ── !vippick ─────────────────────────────────────────────────────────
    @commands.command(name="vippick")
    @is_admin_or_owner()
    @commands.guild_only()
    async def vippick(self, ctx: commands.Context, sport: str, away_team: str, home_team: str,
                       picked_team: str, kalshi_price: float):
        sport_code = resolve_sport(sport)
        if sport_code is None:
            await ctx.send(f"⚠️ Unknown sport `{sport}`. Use MLB, NFL, NBA, \"College Football\", or \"College Basketball\".")
            return

        if not (0 < kalshi_price < 100):
            await ctx.send("⚠️ Kalshi price must be between 1 and 99 (cents).")
            return

        channel = self._find_channel(ctx.guild, config.CH_VIP_PICKS)
        if channel is None:
            await ctx.send(f"⚠️ Couldn't find #{config.CH_VIP_PICKS}. Run `!setup` first.")
            return

        data = self.store.load()
        await append_line(channel, data["daily_picks"]["vip"], "VIP PICKS", build_pick_line(picked_team))
        data["pending_picks"].append({
            "sport": sport_code, "away": away_team, "home": home_team,
            "picked": picked_team, "type": "vip", "price": kalshi_price,
        })
        self.store.save(data)

        await self._cleanup_invocation(ctx)
        if channel.id != ctx.channel.id:
            await ctx.send(f"✅ VIP pick posted in {channel.mention}.", delete_after=5)

    # ── !editpick ────────────────────────────────────────────────────────
    @commands.command(name="editpick")
    @is_admin_or_owner()
    @commands.guild_only()
    async def editpick(self, ctx: commands.Context, sport: str, away_team: str, home_team: str,
                        old_picked_team: str, new_picked_team: str):
        """Fixes a typo'd/wrong picked team on a pick that's already posted:
        updates the tracked pending pick (so !result auto-calc still matches
        it correctly) AND edits the corresponding line in today's live
        rollup message — this is the only way to change it, since users
        can't hand-edit the bot's own message in Discord."""
        sport_code = resolve_sport(sport)
        if sport_code is None:
            await ctx.send(f"⚠️ Unknown sport `{sport}`. Use MLB, NFL, NBA, \"College Football\", or \"College Basketball\".")
            return

        data = self.store.load()
        idx = None
        for i, p in enumerate(data["pending_picks"]):
            if (p["sport"] == sport_code
                    and p["away"].lower() == away_team.lower()
                    and p["home"].lower() == home_team.lower()
                    and p["picked"].lower() == old_picked_team.lower()):
                idx = i
                break

        if idx is None:
            await ctx.send(
                "⚠️ Couldn't find a pending pick matching that sport/teams/old picked team. "
                "Run `!pending` to check exactly what's stored."
            )
            return

        pick = data["pending_picks"][idx]
        old_line = build_pick_line(pick["picked"])
        pick["picked"] = new_picked_team
        new_line = build_pick_line(new_picked_team)

        is_free = pick["type"] == "free"
        slot = data["daily_picks"]["free" if is_free else "vip"]

        if old_line in slot["lines"]:
            slot["lines"][slot["lines"].index(old_line)] = new_line
            channel = self._find_channel(ctx.guild, config.CH_FREE_PICKS if is_free else config.CH_VIP_PICKS)
            if channel:
                await resync(channel, slot, "FREE PICKS" if is_free else "VIP PICKS")
            self.store.save(data)
            await ctx.send(f"✅ Updated the pick to **{new_picked_team}** — tracking and today's message both fixed.")
        else:
            self.store.save(data)
            await ctx.send(
                f"✅ Updated the tracked pick to **{new_picked_team}**, but couldn't find the exact matching "
                "line in today's rollup message to edit (it may already be a different day, or already "
                "resolved) — the message itself may need a manual look."
            )

    # ── shared error handling ───────────────────────────────────────────
    @freepick.error
    @vippick.error
    @editpick.error
    async def picks_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 Only the Phantom Picks admin can post picks.")
        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.send(f"⚠️ Missing or invalid argument. Check `!help` for exact syntax.\n`{error}`")
        else:
            await ctx.send(f"⚠️ Something went wrong: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Picks(bot))
