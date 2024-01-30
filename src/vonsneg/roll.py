"""
vonsneg.roll
~~~~~~~~~~~~
Module for simulating rolls
"""
import numpy as np


def roll(dice: int, target_number: int) -> int:
    """Rolls {dice}D6 and returns the number >= {target_number}."""
    results = np.random.randint(1, 7, size=dice)
    return (results >= target_number).sum()
