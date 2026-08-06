"""Custom !help command listing every Phantom Picks command and its syntax."""
from discord.ext import commands

import config

HELP_TEXT = """\
👻 **PHANTOM PICKS — COMMANDS**

**Pick posting** *(admin only)*
`!freepick [sport] [away team] [home team] [picked team] [kalshi price] [model probability]`
Posts a formatted free pick to #free-daily-picks.
Example: `!freepick MLB "New York Yankees" "Boston Red Sox" "Boston Red Sox" 62 68`

`!vippick [sport] [away team] [home team] [picked team] [kalshi price] [model probability] [edge]`
Posts a formatted VIP pick to #vip-picks. Recommended bet is always shown as "1 unit" (see `!setunits`/Unit size note below).
Example: `!vippick MLB "New York Yankees" "Boston Red Sox" "Boston Red Sox" 62 68 6`

**Results & record** *(admin only unless noted)*
`!result [W|L] [sport] [away team] [home team] [picked team] [amount|auto] [notes]`
Posts the result to #free-results if that pick came from `!freepick`, or #vip-results if it came from `!vippick` (posts to both only if the pick's origin can't be matched), and updates the pinned model record.
For `[amount]`, either type a dollar figure yourself, **or type `auto`** to have the bot calculate both the $ profit/loss and the units change automatically from that pick's Kalshi price (assumes a flat 1-unit stake on every game — see `!help` unit size note below). `auto` only works if the sport/teams/picked team match a pick you posted with `!freepick`/`!vippick` exactly.
Example (auto): `!result W MLB "New York Yankees" "Boston Red Sox" "Boston Red Sox" auto "Bullpen shut the door in the 8th"`
Example (manual): `!result W MLB "New York Yankees" "Boston Red Sox" "Boston Red Sox" 46 "Bullpen shut the door in the 8th"`

`!updaterecord [W|L] [sport]` — manually add a win/loss to the overall + sport record.
Example: `!updaterecord W NFL`

`!setrecord [W-L]` — manually set the overall record.
Example: `!setrecord 45-30`

`!setunits [+/-X]` — manually overwrite (not add to) the units total shown in the pinned record. Not needed if you're using `auto` on `!result` — that already adjusts units for you.
Example: `!setunits +12.5`

`!record` — **anyone** can use this. Posts the current model record block.

`!pending` — lists every pick still awaiting a `!result` (sport, teams, picked team, price, free/VIP) — useful for checking exactly what the bot has stored if `auto` can't find a match.

`!clearpending [sport] [away team] [home team] [picked team]` — removes every pending entry matching those details. Use this to clear out duplicate posts of the same pick, or a stale/priceless entry. Check `!pending` first to see what's there.

**Setup** *(admin only)*
`!setup` — (re)creates all categories/channels/roles/permissions and pinned messages.

**Sports accepted:** MLB, NFL, NBA, "College Football" (or CFB), "College Basketball" (or CBB)

**Unit size:** 1 unit = ${unit_size:g}. Used by `!result ... auto ...` to calculate P&L/units from the Kalshi price, assuming a flat 1-unit stake every game.

💡 Wrap any argument that contains spaces (team names, sport names, notes/reasons) in "double quotes".
⚠️ Not financial advice. Bet responsibly.
"""


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context):
        await ctx.send(HELP_TEXT.format(unit_size=config.UNIT_SIZE))


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
