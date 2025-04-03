"""
vonsneg.types
~~~~~~~~~~~~~
typing for different units
"""
from typing import TypedDict, List


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
    rules: List[str]
    type: str

