"""
vonsneg.shooting
~~~~~~~~~~~~~~~~
module for simulating shooting attacks
"""
from vonsneg.roll import roll
from vonsneg.types import Unit

def attack(
    unit: Unit, target_vulnurability: int, weapon: str = "Black Powder", skirmish: bool = False
) -> int:
    """
    Unit rolls models dice against its innacuraccy to get succesful hits,
    then saves are rolled using the target's vulnurability.
    """
    attacks = unit["models"]
    hit_modifier = 0
    if skirmish is True:
        modifier += 2
    to_wound = roll(attacks, unit["innaccuracy"] + hit_modifier)
    wound_modifier = 0
    if weapon == "Missile":
        wound_modifier -= 2
    
    return to_wound - roll(to_wound, target_vulnurability + wound_modifier)