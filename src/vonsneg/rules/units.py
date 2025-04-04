from dataclasses import dataclass
from typing import List, Dict
import json
from pathlib import Path
from typing import Dict

@dataclass
class BaseUnit:
    name: str
    unit_type: str
    models: int
    base_size: str
    stats: Dict[str, int]
    traits: List[str]

    def attacks_per_model(self) -> int:
        return self.stats.get("A", 0)

    def inaccuracy(self) -> int:
        return self.stats.get("I", 6)

    def total_attacks(self) -> int:
        return self.models * self.attacks_per_model()

    def is_fearless(self) -> bool:
        return "Fearless" in self.traits


def load_units_from_json(filepath: str = "data/units.json") -> Dict[str, BaseUnit]:
    with open(Path(filepath), "r", encoding="utf-8") as f:
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
        )
        units[unit.name.lower()] = unit  # store by lowercase name for easy lookup

    return units
