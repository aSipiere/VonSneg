from vonsneg.rules.units import load_units_from_json
from vonsneg.rules.melee import MeleeCombatSimulator

from pathlib import Path


# This gets you the root of the repo, regardless of where the script is run from
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


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

    print("\nChoose defender:")
    defender = choose_unit(units)

    print(f"\nSimulating combat between {attacker.name} and {defender.name}...\n")
    sim = MeleeCombatSimulator.from_units(attacker, defender)
    print(sim.describe())


if __name__ == "__main__":
    main()
