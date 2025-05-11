from pathlib import Path

from vonsneg.rules.melee import MeleeCombatSimulator
from vonsneg.rules.units import load_units_from_json
from vonsneg.rules.weapons import (BlackPowderWeapon, CloseCombatWeapon,
                                   MissileWeapon, PistolAndSabre)

# This gets you the root of the repo, regardless of where the script is run from
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Map of available weapons
WEAPONS = {
    "close combat": CloseCombatWeapon,
    "black powder": BlackPowderWeapon,
    "missile": MissileWeapon,
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
        weapon.can_shoot = lambda state: not (has_smoke_token == 'yes')  # Update shooting condition based on smoke token
    
    return weapon


def choose_unit(units: dict[str, 'BaseUnit']) -> 'BaseUnit':
    print("\nAvailable units:")
    for name in units:
        print(f" - {name}")
    print()
    choice = input("Enter unit name: ").strip().lower()
    if choice not in units:
        raise ValueError(f"Unit '{choice}' not found.")
    return units[choice]

def main():
    print("Loading units...")
    units = load_units_from_json(DATA / "core_units.json")  # should return dict[str, BaseUnit]

    print("\nChoose attacker:")
    attacker = choose_unit(units)
    attacker.weapon = choose_weapon()  # Allow weapon selection for the attacker

    print("\nChoose defender:")
    defender = choose_unit(units)
    defender.weapon = choose_weapon()  # Allow weapon selection for the defender

    print(f"\nSimulating combat between {attacker.name} and {defender.name}...\n")
    sim = MeleeCombatSimulator.from_units(attacker, defender)
    print(sim.describe())


if __name__ == "__main__":
    main()
