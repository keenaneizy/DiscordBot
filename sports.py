"""Sport name resolution — turns free-typed user input into a canonical sport code."""
import config


def resolve_sport(raw: str):
    """Return the canonical sport code (e.g. 'MLB') for a user-typed sport
    string, or None if it doesn't match any known alias."""
    key = raw.strip().lower()
    return config.SPORT_ALIASES.get(key)
