"""
Picks cog — !freepick and !vippick.

Both commands take quoted arguments for anything that can contain spaces
(sport names like "College Football", team names, the VIP reason text).
See !help (cogs/help.py) or README.md for exact syntax and examples.
"""
import discord
from discord.ext import commands

import config
from checks import is_admin_or_owner
from data_store import DataStore
from formatting import build_free_pick_message, build_vip_pick_message
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
                        picked_team: str, kalshi_price: float, model_probability: float):
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

        message = build_free_pick_message(sport_code, away_team, home_team, picked_team,
                                           kalshi_price, model_probability)
        await channel.send(message)

        data = self.store.load()
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
                       picked_team: str, kalshi_price: float, model_probability: float, edge: float):
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

        message = build_vip_pick_message(sport_code, away_team, home_team, picked_team,
                                          kalshi_price, model_probability, edge)
        await channel.send(message)

        data = self.store.load()
        data["pending_picks"].append({
            "sport": sport_code, "away": away_team, "home": home_team,
            "picked": picked_team, "type": "vip", "price": kalshi_price,
        })
        self.store.save(data)

        await self._cleanup_invocation(ctx)
        if channel.id != ctx.channel.id:
            await ctx.send(f"✅ VIP pick posted in {channel.mention}.", delete_after=5)

    # ── shared error handling ───────────────────────────────────────────
    @freepick.error
    @vippick.error
    async def picks_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 Only the Phantom Picks admin can post picks.")
        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.send(f"⚠️ Missing or invalid argument. Check `!help` for exact syntax.\n`{error}`")
        else:
            await ctx.send(f"⚠️ Something went wrong: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Picks(bot))
