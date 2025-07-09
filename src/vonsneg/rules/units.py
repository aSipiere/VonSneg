import json
from dataclasses import dataclass, field
from pathlib import Path

from vonsneg.rules.weapons import BaseWeapon, CloseCombatWeapon


@dataclass
class BaseUnit:
    name: str
    unit_type: str
    models: int
    base_size: str
    stats: dict[str, int]
    traits: list[str]
    weapon: BaseWeapon
    state: dict = field(default_factory=dict)

    def attacks_per_model(self) -> int:
        return self.stats.get("A", 0)

    def inaccuracy(self) -> int:
        return self.stats.get("I", 6)

    def total_attacks(self) -> int:
        return self.models * self.attacks_per_model()

    def is_fearless(self) -> bool:
        return "Fearless" in self.traits


def load_unit_dicts_from_json(filepath: str = "data/units.json") -> dict[str, dict]:
    """Load unit data as dictionaries (not BaseUnit objects), keyed by lowercase name."""
    with open(Path(filepath), encoding="utf-8") as f:
        data = json.load(f)["units"]
    return {entry["name"].lower(): entry for entry in data}


def load_units_from_json(filepath: str = "data/units.json") -> dict[str, BaseUnit]:
    with open(Path(filepath), encoding="utf-8") as f:
        data = json.load(f)["units"]

    units = {}
    for entry in data:
        unit = BaseUnit(
            name=entry["name"],
            unit_type=entry["type"],
            models=entry["models"],
            base_size=entry["base_size"],
            stats=entry["stats"],
            traits=entry["traits"],
            weapon=CloseCombatWeapon(),  # Default weapon, can be changed later
        )
        units[unit.name.lower()] = unit  # store by lowercase name for easy lookup

    return units
