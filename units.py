"""
Kalshi payout math for automatic P&L / units tracking.

A Kalshi contract costs `price` cents and pays out 100 cents if it resolves
YES, 0 cents if it resolves NO. Assuming a flat 1-unit stake on every pick
(config.UNIT_SIZE dollars), buying UNIT_SIZE dollars worth of contracts at
`price` cents each and winning nets a profit of:

    UNIT_SIZE * (100 - price) / price   dollars

...and losing forfeits the whole UNIT_SIZE stake. In units terms (where 1
unit = UNIT_SIZE dollars), a win is worth (100 - price) / price units and a
loss is always exactly -1 unit, since the whole stake is lost.
"""
import config


def auto_profit(win: bool, price_cents: float) -> float:
    """Dollar amount for a 1-unit stake at the given Kalshi price — a
    positive profit on a win, or the (positive) magnitude of the loss."""
    if win:
        return config.UNIT_SIZE * (100 - price_cents) / price_cents
    return config.UNIT_SIZE


def auto_units_change(win: bool, price_cents: float) -> float:
    """Units gained (positive) or lost (negative) for a 1-unit stake."""
    if win:
        return (100 - price_cents) / price_cents
    return -1.0
