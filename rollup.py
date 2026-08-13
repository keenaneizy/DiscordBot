"""
Daily rollup messages.

Instead of posting a brand-new message for every single !freepick/!vippick/
!result, each channel keeps ONE running message per calendar day listing
every game so far in a compact one-line format, edited in place as new
lines are appended. The first pick/result posted on a new calendar date
automatically starts a fresh message.
"""
import datetime

import discord


def today_key() -> str:
    return datetime.date.today().isoformat()


def today_display() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%b %d, %Y")


def _render(slot: dict, label: str) -> str:
    return f"👻 PHANTOM PICKS — {label} — {today_display()}\n" + "\n".join(slot["lines"])


async def append_line(channel: discord.TextChannel, slot: dict, label: str, line: str) -> None:
    """Mutates `slot` (a dict with date/channel_id/message_id/lines keys,
    e.g. data["daily_picks"]["vip"]) in place to add `line`, starting a
    fresh message if the date rolled over since its last use, then sends or
    edits the message in `channel`. The caller is responsible for saving
    the owning DataStore data afterward."""
    today = today_key()
    if slot.get("date") != today:
        slot["date"] = today
        slot["message_id"] = None
        slot["lines"] = []

    slot["lines"].append(line)

    message = None
    if slot.get("message_id"):
        try:
            message = await channel.fetch_message(slot["message_id"])
        except (discord.NotFound, discord.HTTPException):
            message = None

    if message is None:
        message = await channel.send(_render(slot, label))
        slot["message_id"] = message.id
        slot["channel_id"] = channel.id
    else:
        await message.edit(content=_render(slot, label))


async def resync(channel: discord.TextChannel, slot: dict, label: str) -> None:
    """Re-renders and edits the existing message for this slot from its
    current `lines` — used to fix a line already appended (see !editpick)
    without adding a new one. No-op if there's no message tracked yet."""
    if not slot.get("message_id"):
        return
    try:
        message = await channel.fetch_message(slot["message_id"])
    except (discord.NotFound, discord.HTTPException):
        return
    await message.edit(content=_render(slot, label))
