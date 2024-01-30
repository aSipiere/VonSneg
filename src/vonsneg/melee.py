"""
vonsneg.melee
~~~~~~~~~~~~~
module for melee simulation
"""
from typing import Union

from vonsneg.roll import roll
from vonsneg.types import Unit


def attack(
    unit: Unit, target_vulnurability: int, close_combat_weapon: bool = False
) -> int:
    """
    Unit rolls models * attacks dice against its innacuraccy to get succesful hits,
    then saves are rolled using the target's vulnurability.
    """
    attacks = unit["models"] * unit["attacks"]
    if close_combat_weapon is True:
        to_wound = roll(attacks, unit["innaccuracy"] - 1)
    else:
        to_wound = roll(attacks, unit["innaccuracy"])
    return to_wound - roll(to_wound, target_vulnurability)


def get_models_remaining(unit: dict) -> int:
    """Get the remaining models from wounds taken and wounds per model."""
    return (unit["models"] * unit["wounds"] - unit["wounds_taken"]) // unit["wounds"]


def melee(
    charging_unit: Unit,
    defending_unit: Unit,
    can_shoot: Union[bool, str] = False,
    bouts=1,
) -> dict:
    """simulate melee"""
    if "wounds_taken" not in charging_unit.keys():
        charging_unit["wounds_taken"] = 0
        defending_unit["wounds_taken"] = 0

    charging_models_remaining = get_models_remaining(charging_unit)
    defending_models_remaining = get_models_remaining(defending_unit)
    if can_shoot is not False:
        raise NotImplementedError("No support for stand and fire")
    defending_unit["wounds_taken"] += attack(
        charging_unit, defending_unit["vulnurability"], close_combat_weapon=False
    )
    defending_models_remaining -= (
        defending_unit["wounds_taken"] // defending_unit["wounds"]
    )
    if defending_models_remaining <= 0:
        return {
            "winner": "Charger",
            "charging_wounds_delivered": defending_unit["models"]
            * defending_unit["wounds"],
            "defending_wounds_delivered": charging_unit["wounds_taken"],
            "bouts": bouts,
        }
    charging_unit["wounds_taken"] = attack(
        defending_unit,
        charging_unit["vulnurability"],
        close_combat_weapon=False,
    )
    charging_models_remaining -= (
        charging_unit["wounds_taken"] // charging_unit["wounds"]
    )

    if charging_unit["wounds_taken"] == defending_unit["wounds_taken"]:
        print("another round")
        bouts += 1
        return melee(charging_unit, defending_unit, can_shoot, bouts)
    if defending_unit["wounds_taken"] > charging_unit["wounds_taken"]:
        winner = "Charger"
    else:
        winner = "Defender"
    return {
        "winner": winner,
        "charging_wounds_delivered": defending_unit["wounds_taken"],
        "defending_wounds_delivered": charging_unit["wounds_taken"],
        "bouts": bouts,
    }
