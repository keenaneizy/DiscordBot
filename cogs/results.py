"""
Results cog — score-tracking commands.

!result        posts a result to both public results channels and updates
               every record bucket (overall, sport, today, and — if it can
               be correlated to a pick posted via !vippick — confidence tier)
!updaterecord  manual overall + sport record correction (no channel post)
!setrecord     manually overwrite the overall W-L
!setunits      manually overwrite the units total
!record        anyone can ask for the current record block

Note on confidence tracking: !result's syntax (per spec) doesn't take a
confidence argument, and only !vippick picks have a confidence tier at all
(!freepick picks don't). So when !result runs, it looks for a matching entry
in data["pending_picks"] (same sport/away/home/picked, case-insensitive) to
find out if this game's pick had a confidence tier, and only then updates
the HIGH/MEDIUM buckets. If no match is found (e.g. the pick was posted
before a bot restart cleared pending picks, or it was a free-only pick),
the confidence buckets are simply left untouched — overall/sport/today
records are still updated regardless.

Note on the `amount` argument: pass a dollar figure to book it manually, or
pass the literal word `auto` to have the bot calculate both the dollar P&L
and the units change itself from the Kalshi price stored on the matching
pending pick, assuming a flat 1-unit stake (config.UNIT_SIZE dollars) on
every game — see units.py for the payout math. `auto` only works when a
matching pending pick with a saved price exists.
"""
import datetime

import discord
from discord.ext import commands

import config
from checks import is_admin_or_owner
from data_store import DataStore
from formatting import build_free_result_message, build_vip_result_message, build_record_block, fmt_num
from sports import resolve_sport
from units import auto_profit, auto_units_change


class Results(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store = DataStore()

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _today_key() -> str:
        return datetime.date.today().isoformat()

    def _roll_today(self, data: dict) -> dict:
        today = data["today"]
        current = self._today_key()
        if today.get("date") != current:
            data["today"] = {"date": current, "wins": 0, "losses": 0}
        return data

    @staticmethod
    def _find_pending(data: dict, sport_code: str, away: str, home: str, picked: str):
        for i, pick in enumerate(data["pending_picks"]):
            if (pick["sport"] == sport_code
                    and pick["away"].lower() == away.lower()
                    and pick["home"].lower() == home.lower()
                    and pick["picked"].lower() == picked.lower()):
                return i
        return None

    async def _refresh_pin(self, guild: discord.Guild, data: dict):
        setup_cog = self.bot.get_cog("ServerSetup")
        record_channel = discord.utils.get(guild.text_channels, name=config.CH_MODEL_RECORD)
        if setup_cog and record_channel:
            await setup_cog.sync_record_pin(record_channel)

    # ── !result ──────────────────────────────────────────────────────────
    @commands.command(name="result")
    @is_admin_or_owner()
    @commands.guild_only()
    async def result(self, ctx: commands.Context, outcome: str, sport: str, away_team: str,
                      home_team: str, picked_team: str, amount: str, notes: str):
        outcome = outcome.strip().upper()
        if outcome not in ("W", "L"):
            await ctx.send("⚠️ Result must be `W` or `L`.")
            return

        sport_code = resolve_sport(sport)
        if sport_code is None:
            await ctx.send(f"⚠️ Unknown sport `{sport}`. Use MLB, NFL, NBA, \"College Football\", or \"College Basketball\".")
            return

        win = outcome == "W"
        bucket_key = "wins" if win else "losses"

        data = self.store.load()
        data = self._roll_today(data)

        # Pull the matching pending pick (if any) *before* deciding the
        # amount, since auto-calculation needs its stored Kalshi price.
        pending_idx = self._find_pending(data, sport_code, away_team, home_team, picked_team)
        pending_pick = data["pending_picks"][pending_idx] if pending_idx is not None else None

        units_change = None  # only set when auto-calculating from a Kalshi price

        if amount.strip().lower() in ("auto", "a", "-"):
            if pending_pick is None or pending_pick.get("price") is None:
                await ctx.send(
                    "⚠️ Can't auto-calculate — no matching pending pick with a saved Kalshi price was "
                    "found (sport/teams/picked team have to match the original !freepick or !vippick "
                    "exactly). Enter the dollar amount manually instead of `auto`."
                )
                return
            price = pending_pick["price"]
            amount_value = auto_profit(win, price)
            units_change = auto_units_change(win, price)
        else:
            try:
                amount_value = abs(float(amount))
            except ValueError:
                await ctx.send("⚠️ Amount must be a number, or type `auto` to calculate it from the Kalshi price.")
                return

        data["overall"][bucket_key] += 1
        data["sports"][sport_code][bucket_key] += 1
        data["today"][bucket_key] += 1
        data["pnl"] += amount_value if win else -amount_value
        if units_change is not None:
            data["units"] += units_change

        if pending_idx is not None:
            pick = data["pending_picks"].pop(pending_idx)
            if pick.get("confidence") in ("HIGH", "MEDIUM"):
                data["confidence"][pick["confidence"]][bucket_key] += 1

        self.store.save(data)

        free_msg = build_free_result_message(win, sport_code, away_team, home_team, picked_team,
                                              data["today"], data["overall"])
        vip_msg = build_vip_result_message(win, sport_code, away_team, home_team, picked_team,
                                            amount_value, data["today"], data["overall"], notes)

        free_results_ch = discord.utils.get(ctx.guild.text_channels, name=config.CH_FREE_RESULTS)
        vip_results_ch = discord.utils.get(ctx.guild.text_channels, name=config.CH_VIP_RESULTS)

        if free_results_ch:
            await free_results_ch.send(free_msg)
        if vip_results_ch:
            await vip_results_ch.send(vip_msg)

        await self._refresh_pin(ctx.guild, data)

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

    # ── !updaterecord ────────────────────────────────────────────────────
    @commands.command(name="updaterecord")
    @is_admin_or_owner()
    @commands.guild_only()
    async def updaterecord(self, ctx: commands.Context, outcome: str, sport: str):
        outcome = outcome.strip().upper()
        if outcome not in ("W", "L"):
            await ctx.send("⚠️ Result must be `W` or `L`.")
            return

        sport_code = resolve_sport(sport)
        if sport_code is None:
            await ctx.send(f"⚠️ Unknown sport `{sport}`. Use MLB, NFL, NBA, \"College Football\", or \"College Basketball\".")
            return

        bucket_key = "wins" if outcome == "W" else "losses"
        data = self.store.load()
        data["overall"][bucket_key] += 1
        data["sports"][sport_code][bucket_key] += 1
        self.store.save(data)

        await self._refresh_pin(ctx.guild, data)
        await ctx.send(
            f"✅ Recorded a {'win' if outcome == 'W' else 'loss'} for {config.SPORT_INFO[sport_code]['name']}. "
            f"Overall now {data['overall']['wins']}-{data['overall']['losses']}."
        )

    # ── !setrecord ───────────────────────────────────────────────────────
    @commands.command(name="setrecord")
    @is_admin_or_owner()
    @commands.guild_only()
    async def setrecord(self, ctx: commands.Context, record: str):
        try:
            wins_str, losses_str = record.split("-")
            wins, losses = int(wins_str), int(losses_str)
        except ValueError:
            await ctx.send("⚠️ Format must be `W-L`, e.g. `!setrecord 45-30`.")
            return

        data = self.store.load()
        data["overall"] = {"wins": wins, "losses": losses}
        self.store.save(data)

        await self._refresh_pin(ctx.guild, data)
        await ctx.send(f"✅ Overall record set to {wins}-{losses}.")

    # ── !setunits ────────────────────────────────────────────────────────
    @commands.command(name="setunits")
    @is_admin_or_owner()
    @commands.guild_only()
    async def setunits(self, ctx: commands.Context, units: float):
        data = self.store.load()
        data["units"] = units
        self.store.save(data)

        await self._refresh_pin(ctx.guild, data)
        await ctx.send(f"✅ Units set to {fmt_num(units)}.")

    # ── !record ──────────────────────────────────────────────────────────
    @commands.command(name="record")
    async def record(self, ctx: commands.Context):
        data = self.store.load()
        await ctx.send(build_record_block(data))

    # ── error handling for every command in this cog ───────────────────
    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 Only the Phantom Picks admin can use this command.")
        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.send(f"⚠️ Missing or invalid argument. Check `!help` for exact syntax.\n`{error}`")
        else:
            await ctx.send(f"⚠️ Something went wrong: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Results(bot))
