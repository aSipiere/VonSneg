"""
vonsneg.types
~~~~~~~~~~~~~
typing for different units
"""
from typing import TypedDict


class Unit(TypedDict):
    """
    Base Unit Class
    """

    name: str
    models: int
    movement: int
    attacks: int
    innacuracy: int
    wounds: int
    vulnurability: int


class CombatUnit(Unit):
    """
    Extended unit class to hold things like current wounds and panic
    """
