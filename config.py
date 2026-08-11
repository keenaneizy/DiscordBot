"""
Central configuration for the Phantom Picks bot.

Edit values here to rename channels/categories/roles or tweak sport
metadata without touching logic anywhere else in the codebase.
"""
import os

# ── Bot / environment ────────────────────────────────────────────────
COMMAND_PREFIX = "!"

# Optional extra owner override (a Discord user ID string). The guild owner
# and anyone with the Administrator permission can already use admin-only
# commands without this being set — see checks.py.
BOT_OWNER_ID = os.getenv("BOT_OWNER_ID")

# Phantom Pro upgrade link (override via WINIBLE_LINK in .env if it changes)
WINIBLE_LINK = os.getenv("WINIBLE_LINK", "https://www.winible.com/phantompicks1")

SOCIAL_HANDLE = "@phantompicks"

# Dollar value of 1 "unit" — used to auto-calculate P&L and units change from
# the Kalshi price when !result is run with `auto` as the amount. Assumes a
# flat 1-unit stake on every pick. Change via the UNIT_SIZE env var any time
# (e.g. as your bankroll grows) without needing a code change.
UNIT_SIZE = float(os.getenv("UNIT_SIZE", "200"))

# ── Category names (created in this exact order) ─────────────────────
CAT_INFO = "📋 INFORMATION"
CAT_RECORD = "📊 MODEL RECORD"
CAT_FREE = "🆓 FREE PICKS"
CAT_VIP = "💎 VIP MEMBERS ONLY"

# ── Channel names ──────────────────────────────────────────────────────
CH_WELCOME = "welcome"
CH_UNIT_SIZING = "unit-sizing-and-responsible-betting"
CH_MODEL_RECORD = "model-record-and-pnl"
CH_FREE_PICKS = "free-daily-picks"
CH_FREE_RESULTS = "free-results"
CH_FREE_CHAT = "free-chat"
CH_MEMBER_WINS = "member-wins"
CH_VIP_PICKS = "vip-picks"
CH_VIP_RESULTS = "vip-results"
CH_VIP_CHAT = "vip-chat"

# ── Roles ────────────────────────────────────────────────────────────
ROLE_FREE = "Free Member"
ROLE_VIP = "Phantom Pro"  # Membership managed externally by Winible

# ── Sports ───────────────────────────────────────────────────────────
# Every accepted alias (lowercase) -> canonical sport code.
# Add more aliases here if you want e.g. "ncaaf"/"ncaab" style shortcuts.
SPORT_ALIASES = {
    "mlb": "MLB",
    "baseball": "MLB",
    "nfl": "NFL",
    "football": "NFL",
    "nba": "NBA",
    "basketball": "NBA",
    "cfb": "CFB",
    "ncaaf": "CFB",
    "college football": "CFB",
    "cbb": "CBB",
    "ncaab": "CBB",
    "college basketball": "CBB",
}

SPORT_INFO = {
    "MLB": {"emoji": "⚾", "name": "MLB"},
    "NFL": {"emoji": "🏈", "name": "NFL"},
    "NBA": {"emoji": "🏀", "name": "NBA"},
    "CFB": {"emoji": "🎓🏈", "name": "College Football"},
    "CBB": {"emoji": "🎓🏀", "name": "College Basketball"},
}

# Fixed display order for the model record block
SPORT_ORDER = ["MLB", "NFL", "NBA", "CFB", "CBB"]
