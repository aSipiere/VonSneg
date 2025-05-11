from collections import defaultdict
from typing import Dict

from icepool import Pool, d6

from vonsneg.dice.roller import Roller
from vonsneg.rules.units import BaseUnit
from vonsneg.rules.weapons import BlackPowderWeapon


def shooting_attack(shooter: BaseUnit, target: BaseUnit, powder_smoke: bool = False, stand_and_shoot: bool = False) -> Dict[int, float]:
    """
    Simulate a shooting attack using Icepool for distributions, without panic token.

    :param shooter: The attacking unit (BaseUnit).
    :param target: The target unit (BaseUnit).
    :param powder_smoke: Whether the shooter has a powder smoke token.
    :param stand_and_shoot: Whether this is a stand and shoot reaction.
    :return: A dictionary of {wounds: probability} for all outcomes.
    """

    # Step 1: Get the weapon being used (default to first equipped weapon)

    # Step 2: Check if the weapon can shoot
    if isinstance(shooter.weapon, BlackPowderWeapon):
        if not shooter.weapon.can_shoot({"smoke": powder_smoke}):
            print(f"{shooter.name} cannot shoot because of powder smoke.")
            return {0: 1.0}  # No wounds, as they can't shoot

    # Step 3: Generate the dice for to-hit rolls based on the shooter's inaccuracy
    to_hit_roller = Roller(num_dice=shooter.models, target=shooter.inaccuracy())
    hit_distribution = to_hit_roller.prob_dict()  # Get the probability distribution for hits

    # Step 4: Generate the dice for to-wound rolls based on the target's vulnerability
    wound_distribution = defaultdict(float)  # Using defaultdict to accumulate probabilities
    hit_occurred = False  # To track if any hits were made

    for hits, prob_hit in hit_distribution.items():
        if hits > 0:  # Only proceed with to-wound if there are hits
            hit_occurred = True  # Set flag if there are hits
            to_wound_roller = Roller(num_dice=hits, target=target.stats.get("V", 6))
            wound_dist = to_wound_roller.prob_dict()

            for wounds, prob_wound in wound_dist.items():
                # Calculate total wounds
                wound_distribution[wounds] += prob_hit * prob_wound

    # Step 5: Apply wounds and calculate casualties
    total_wounds = sum(wounds * prob for wounds, prob in wound_distribution.items())
    total_casualties = total_wounds // target.stats.get("W", 1)

    target.models -= total_casualties

    # Return the outcome distribution
    outcome_dist = defaultdict(float)
    for wounds, prob in wound_distribution.items():
        outcome_dist[wounds] = prob

    return outcome_dist
