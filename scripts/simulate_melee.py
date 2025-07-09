# ruff: noqa
from pathlib import Path

from vonsneg.rules.melee import MeleeSimulator
from vonsneg.rules.units import BaseUnit, load_unit_dicts_from_json
from vonsneg.rules.weapons import (
    BaseWeapon,
    BlackPowderWeapon,
    CloseCombatWeapon,
    MissileWeapon,
    OldMissileWeapon,
    PistolAndSabre,
)

# This gets you the root of the repo, regardless of where the script is run from
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Map of available weapons
WEAPONS = {
    "close combat": CloseCombatWeapon,
    "black powder": BlackPowderWeapon,
    "missile": MissileWeapon,
    "old missile": OldMissileWeapon,
    "pistol and sabre": PistolAndSabre,
}


def choose_weapon() -> BaseWeapon:
    print("\nAvailable weapons:")
    for weapon_name in WEAPONS:
        print(f" - {weapon_name}")
    print()
    choice = input("Enter weapon name: ").strip().lower()
    if choice not in WEAPONS:
        raise ValueError(f"Weapon '{choice}' not found.")

    weapon = WEAPONS[choice]()  # Create the weapon instance

    # If the weapon is a Black Powder weapon, ask about powder smoke
    if isinstance(weapon, BlackPowderWeapon):
        has_smoke_token = input("Does the unit have a powder smoke token? (yes/no): ").strip().lower()
        if has_smoke_token == "yes":
            # Override the can_shoot method to check for smoke
            original_can_shoot = weapon.can_shoot
            weapon.can_shoot = lambda unit_state=None: original_can_shoot({"smoke": True})

    return weapon


def choose_unit(unit_dicts: dict) -> BaseUnit:
    print("\nAvailable units:")
    for name in unit_dicts:
        print(f" - {name}")
    print()
    choice = input("Enter unit name: ").strip().lower()
    if choice not in unit_dicts:
        raise ValueError(f"Unit '{choice}' not found")
    unit_data = unit_dicts[choice]
    weapon = choose_weapon()
    return BaseUnit(
        name=unit_data["name"],
        unit_type=unit_data["type"],
        models=unit_data["models"],
        base_size=unit_data["base_size"],
        stats=unit_data["stats"],
        traits=unit_data["traits"],
        weapon=weapon,
    )


def main():
    print("Loading units...")
    unit_dicts = load_unit_dicts_from_json(DATA / "core_units.json")

    print("\nChoose attacker:")
    attacker = choose_unit(unit_dicts)

    print("\nChoose defender:")
    defender = choose_unit(unit_dicts)

    print(f"\nSimulating melee combat between {attacker.name} and {defender.name}...\n")
    sim = MeleeSimulator(attacker, defender)
    print(sim.describe())

    # Show some additional details
    print("\n" + "=" * 50)
    print("DETAILED ANALYSIS")
    print("=" * 50)

    result = sim.get_result()
    print(f"Result distribution: {result}")

    # Calculate some statistics
    expected_net_wounds = sum(wounds * prob for wounds, prob in result.items())
    print(f"Expected net wounds: {expected_net_wounds:.2f}")

    # Show win/loss breakdown
    attacker_wins = sum(prob for wounds, prob in result.items() if wounds > 0)
    defender_wins = sum(prob for wounds, prob in result.items() if wounds < 0)
    draws = sum(prob for wounds, prob in result.items() if wounds == 0)

    print(f"Attacker wins: {attacker_wins:.1%}")
    print(f"Defender wins: {defender_wins:.1%}")
    print(f"Draws: {draws:.1%}")


if __name__ == "__main__":
    main()
