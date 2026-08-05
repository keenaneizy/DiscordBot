"""
JSON-backed persistence for Phantom Picks model record data.

All reads/writes go through DataStore so the on-disk schema only needs to be
understood in one place. The file lives at data/record.json (created
automatically on first run) and survives bot restarts as long as the hosting
platform gives the data/ folder a persistent disk (see README.md).
"""
import json
import os
import threading

import config

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_PATH = os.path.join(DATA_DIR, "record.json")


def _default_data() -> dict:
    return {
        "overall": {"wins": 0, "losses": 0},
        "units": 0.0,
        "pnl": 0.0,
        "sports": {code: {"wins": 0, "losses": 0} for code in config.SPORT_ORDER},
        # Rolling "today" counter shown in #free-results, reset automatically
        # whenever the calendar date changes.
        "today": {"date": None, "wins": 0, "losses": 0},
        # Picks posted via !freepick / !vippick, kept here just long enough for
        # !result to look up the Kalshi price of the pick it's resolving (for
        # auto P&L/units calculation). See Results._find_pending() in
        # cogs/results.py.
        "pending_picks": [],
        "pinned_record": {"channel_id": None, "message_id": None},
        "welcome_posted": False,
        "unit_sizing_posted": False,
    }


class DataStore:
    """Thin JSON file wrapper. File I/O here is small and local, so plain
    blocking reads/writes (guarded by a lock) are simpler than an async
    database and are fine for this bot's scale."""

    _lock = threading.Lock()

    def __init__(self, path: str = DATA_PATH):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._write(_default_data())

    def load(self) -> dict:
        with self._lock:
            with open(self.path, "r") as f:
                data = json.load(f)

        # Backfill any keys added in later versions so old record.json files
        # written by an earlier version of the bot keep working.
        changed = False
        for key, value in _default_data().items():
            if key not in data:
                data[key] = value
                changed = True
        for code in config.SPORT_ORDER:
            if code not in data["sports"]:
                data["sports"][code] = {"wins": 0, "losses": 0}
                changed = True
        if changed:
            self.save(data)
        return data

    def save(self, data: dict) -> None:
        with self._lock:
            self._write(data)

    def _write(self, data: dict) -> None:
        # Write to a temp file then atomically replace, so a crash mid-write
        # can never corrupt record.json.
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, self.path)
