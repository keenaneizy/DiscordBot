"""
All outgoing message templates live here, in one place, so the exact visual
format specified for Phantom Picks can be tweaked without hunting through
cog logic.
"""
import datetime

import config

SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


# ── small formatting helpers ─────────────────────────────────────────
def fmt_num(n) -> str:
    """62.0 -> '62', 6.5 -> '6.5' — keeps prices/percentages/edges clean."""
    n = float(n)
    if n.is_integer():
        return str(int(n))
    return f"{n:g}"


def fmt_money(n) -> str:
    """Always two decimals, comma-grouped: 1234.5 -> '1,234.50'."""
    return f"{float(n):,.2f}"


def fmt_units(n) -> str:
    """Always 2 decimal places for the pinned record's units line: 0.694915 -> '0.69'."""
    return f"{float(n):.2f}"


def win_pct(wins: int, losses: int) -> float:
    total = wins + losses
    if total == 0:
        return 0.0
    return round((wins / total) * 100, 1)


def _now_str() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%b %d, %Y %I:%M %p UTC")


# ── pinned informational messages ────────────────────────────────────
def build_welcome_message() -> str:
    return (
        "👻 **WELCOME TO PHANTOM PICKS**\n"
        f"{SEP}\n"
        "Phantom Picks runs a machine learning prediction model that finds "
        "mispriced contracts on Kalshi prediction markets across **MLB, NFL, "
        "NBA, College Football, and College Basketball**.\n\n"
        "Every pick is posted with full transparency — wins **and** losses "
        "are always shown. No cherry picking. Ever.\n"
        f"{SEP}\n"
        "🆓 **FREE MEMBERS GET:**\n"
        "• Occasional free picks\n"
        "• Full model record and P&L tracking in #model-record-and-pnl\n"
        "• Community access, including #free-chat and #member-wins\n\n"
        "💎 **PHANTOM PRO (VIP) MEMBERS GET:**\n"
        "• Early access to ALL picks before games start\n"
        "• Full model data — probability and edge\n"
        "• Recommended bet sizing on every pick\n"
        "• Private VIP community in #vip-chat\n"
        f"{SEP}\n"
        f"💎 Upgrade to Phantom Pro any time at {config.WINIBLE_LINK}\n"
        f"{SEP}\n"
        "⚠️ **Disclaimer:** Phantom Picks is for entertainment and informational "
        "purposes only. Nothing posted in this server is financial advice. "
        "Sports betting and prediction markets carry real financial risk — "
        "only ever bet what you can afford to lose. See "
        f"#{config.CH_UNIT_SIZING} for responsible betting guidance.\n\n"
        f"👻 Follow {config.SOCIAL_HANDLE} for daily free content."
    )


def build_unit_sizing_message() -> str:
    return (
        "👻 **UNIT SIZING & RESPONSIBLE BETTING**\n"
        f"{SEP}\n"
        "**What is a \"unit\"?**\n"
        "A unit is a fixed percentage of your total betting bankroll that you "
        "use as your standard bet size, so every pick is sized consistently "
        "instead of guessed at game by game.\n\n"
        "**How to calculate your unit size:**\n"
        "1. Decide your total betting bankroll — money you've set aside "
        "specifically for betting, separate from bills, savings, etc.\n"
        "2. 1 unit = 1-2% of that bankroll.\n"
        "   _Example: a $1,000 bankroll → 1 unit = $10-$20._\n"
        "3. Use that same unit size on every play unless your model confidence "
        "explicitly calls for scaling up or down.\n"
        f"{SEP}\n"
        "**Bankroll rules:**\n"
        "• Never bet more than 1-2% of your bankroll on a single play.\n"
        "• Never bet money you cannot afford to lose.\n"
        "• Higher confidence picks can justify a slightly larger unit size — "
        "chasing losses with bigger bets is how bankrolls blow up. Don't do it.\n"
        f"{SEP}\n"
        "**Tracking your own P&L:**\n"
        "• Keep a simple spreadsheet or notes log: date, sport, pick, stake, "
        "result, running total.\n"
        "• Compare your personal results against the model record in "
        f"#{config.CH_MODEL_RECORD} — your results will vary based on your "
        "own bet sizing, timing, and the prices you actually get.\n"
        f"{SEP}\n"
        "**Responsible gambling resources:**\n"
        "• National Council on Problem Gambling: 1-800-522-4700 (call/text, 24/7)\n"
        "• ncpgambling.org\n"
        "• Gamblers Anonymous: gamblersanonymous.org\n"
        f"{SEP}\n"
        "⚠️ This is not financial advice. Everything shared in this server is "
        "for informational and entertainment purposes only. Bet responsibly."
    )


def build_welcome_dm() -> str:
    return (
        "👻 Welcome to Phantom Picks\n\n"
        "I run a machine learning prediction model that finds mispriced "
        "contracts on Kalshi prediction markets across MLB, NFL, NBA, "
        "college football, and college basketball.\n\n"
        "Every pick posted with full transparency — wins AND losses always "
        "shown. No cherry picking. Ever.\n\n"
        "🆓 FREE MEMBERS GET:\n"
        "- Occasional free picks\n"
        "- Full model record and P&L tracking\n"
        "- Community access and member wins channel\n\n"
        "💎 PHANTOM PRO VIP MEMBERS GET:\n"
        "- Early access to ALL picks before games start\n"
        "- Full model data — probability and edge\n"
        "- Recommended bet sizing on every pick\n"
        "- Private VIP community\n\n"
        "⚠️ This is not financial advice. Always bet within your means using "
        "proper unit sizing. Never bet money you cannot afford to lose.\n\n"
        f"Follow {config.SOCIAL_HANDLE} on TikTok, Instagram, X, and YouTube "
        "for daily free content.\n\n"
        f"Upgrade to Phantom Pro at {config.WINIBLE_LINK} to unlock VIP access."
    )


# ── model record ──────────────────────────────────────────────────────
def build_record_block(data: dict) -> str:
    overall = data["overall"]
    sports = data["sports"]
    units = data["units"]
    pnl = data["pnl"]

    units_str = f"{'+' if units >= 0 else ''}{fmt_units(units)}"
    pnl_str = f"{'+' if pnl >= 0 else '-'}${fmt_money(abs(pnl))}"

    lines = [
        "👻 PHANTOM PICKS — MODEL RECORD",
        SEP,
        f"📊 Overall Record: {overall['wins']}-{overall['losses']}",
        f"📈 Win Rate: {win_pct(overall['wins'], overall['losses'])}%",
        f"💰 Units: {units_str} units",
        f"💵 P&L: {pnl_str}",
        SEP,
    ]
    for code in config.SPORT_ORDER:
        info = config.SPORT_INFO[code]
        s = sports[code]
        lines.append(f"{info['emoji']} {info['name']}: {s['wins']}-{s['losses']} — {win_pct(s['wins'], s['losses'])}%")
    lines += [
        SEP,
        f"🕐 Last Updated: {_now_str()}",
        "⚠️ Not financial advice. Bet responsibly.",
    ]
    return "\n".join(lines)


# ── daily rollup lines ──────────────────────────────────────────────────
# One of these per game gets appended to that day's running picks/results
# message (see rollup.py) rather than each pick/result getting its own post.
def build_pick_line(picked: str) -> str:
    return f"{picked} ML 1u"


def build_result_line(picked: str, win: bool) -> str:
    outcome = "✅" if win else "❌"
    return f"{picked} ML 1u {outcome}"
