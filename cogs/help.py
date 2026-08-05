"""Custom !help command listing every Phantom Picks command and its syntax."""
from discord.ext import commands

HELP_TEXT = """\
👻 **PHANTOM PICKS — COMMANDS**

**Pick posting** *(admin only)*
`!freepick [sport] [away team] [home team] [picked team] [kalshi price] [model probability]`
Posts a formatted free pick to #free-daily-picks.
Example: `!freepick MLB "New York Yankees" "Boston Red Sox" "Boston Red Sox" 62 68`

`!vippick [sport] [away team] [home team] [picked team] [kalshi price] [model probability] [edge] [HIGH|MEDIUM] [bet size] [reason]`
Posts a formatted VIP pick to #vip-picks.
Example: `!vippick MLB "New York Yankees" "Boston Red Sox" "Boston Red Sox" 62 68 6 HIGH 50 "Bullpen fatigue creates value on the road dog"`

**Results & record** *(admin only unless noted)*
`!result [W|L] [sport] [away team] [home team] [picked team] [profit/loss amount] [notes]`
Posts the result to #free-results and #vip-results, and updates the pinned model record.
Example: `!result W MLB "New York Yankees" "Boston Red Sox" "Boston Red Sox" 46 "Bullpen shut the door in the 8th"`

`!updaterecord [W|L] [sport]` — manually add a win/loss to the overall + sport record.
Example: `!updaterecord W NFL`

`!setrecord [W-L]` — manually set the overall record.
Example: `!setrecord 45-30`

`!setunits [+/-X]` — set the units total shown in the pinned record.
Example: `!setunits +12.5`

`!record` — **anyone** can use this. Posts the current model record block.

**Setup** *(admin only)*
`!setup` — (re)creates all categories/channels/roles/permissions and pinned messages.

**Sports accepted:** MLB, NFL, NBA, "College Football" (or CFB), "College Basketball" (or CBB)

💡 Wrap any argument that contains spaces (team names, sport names, notes/reasons) in "double quotes".
⚠️ Not financial advice. Bet responsibly.
"""


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context):
        await ctx.send(HELP_TEXT)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
