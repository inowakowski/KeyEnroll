"""Random PIN generation."""

from __future__ import annotations

import secrets

DIGITS = "0123456789"


def is_trivial(pin: str) -> bool:
    """Rejects PINs that security keys with PIN complexity enforcement refuse:
    too few distinct characters, or ascending/descending runs like 123456."""
    if len(set(pin)) < min(4, len(pin)):
        return True
    steps = {(ord(b) - ord(a)) % 10 for a, b in zip(pin, pin[1:], strict=False)}
    return steps in ({1}, {9})


def generate_pin(length: int) -> str:
    while True:
        # No leading zero: spreadsheets drop it when the PIN list is exported.
        pin = secrets.choice(DIGITS[1:]) + "".join(
            secrets.choice(DIGITS) for _ in range(length - 1)
        )
        if not is_trivial(pin):
            return pin
