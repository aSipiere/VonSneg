"""vonsneg.units
~~~~~~~~~~~~~
Base class for units and logic for building them from json.
"""

from dataclasses import dataclass, field


@dataclass
class Unit:
    name: str
    models: int
    movement: int
    attacks: int
    inaccuracy: int  # Lower is better (like 6+ to hit)
    wounds: int
    volume: int  # For panic mechanics (V stat)
    melee_first: bool = False
    special_rules: list[str] = field(default_factory=list)

    def is_alive(self) -> bool:
        return self.models > 0
