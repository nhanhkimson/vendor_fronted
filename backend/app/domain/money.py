"""Money in integer cents and rates in basis points (1500 bps = 15%)."""


def allocate(amount: int, weights: list[int]) -> list[int]:
    """Split `amount` proportionally to `weights` by largest remainder.

    The parts always add up to `amount`, unlike rounding each share to two
    decimals (the prototype's `toFixed(2)` split could drift by a cent).
    """
    total = sum(weights)
    if amount <= 0 or total <= 0:
        return [0] * len(weights)
    raw = [amount * w for w in weights]
    shares = [r // total for r in raw]
    remainder = amount - sum(shares)
    order = sorted(range(len(weights)), key=lambda i: (-(raw[i] % total), i))
    for i in order[:remainder]:
        shares[i] += 1
    return shares


def percent_of(amount_cents: int, percent: int) -> int:
    """`percent`% of an amount, rounded half up to the cent."""
    return (amount_cents * percent + 50) // 100


def commission_fee(base_cents: int, rate_bps: int, min_fee_cents: int) -> int:
    """Rate on the base rounded half up, at least the minimum fee, never more than the base."""
    if base_cents <= 0:
        return 0
    fee = (base_cents * rate_bps + 5000) // 10000
    return min(max(fee, min_fee_cents), base_cents)
