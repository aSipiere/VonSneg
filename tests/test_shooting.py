import pytest

from vonsneg.rules.shooting import shooting_attack
from vonsneg.rules.units import BaseUnit
from vonsneg.rules.weapons import MissileWeapon


def test_missile_weapon_with_vulnerability_modifier():
    # Setup: Define a shooter with a Missile Weapon and a target
    shooter = BaseUnit(
        name="Shooter",
        unit_type="Shooter",
        models=5,
        base_size="medium",
        stats={"A": 1, "I": 4, "V": 6},
        traits=[],
        weapon=MissileWeapon()  # Equipped with a Missile Weapon
    )

    target = BaseUnit(
        name="Target",
        unit_type="Target",
        models=10,
        base_size="large",
        stats={"A": 1, "I": 4, "V": 5, "W": 1},
        traits=[],
        weapon=MissileWeapon()
    )
    
    # Test the result when using the MissileWeapon
    outcome = shooting_attack(shooter, target)
    
    assert isinstance(outcome, dict)
    assert sum(outcome.values()) == pytest.approx(1.0, abs=1e-6)  # The probabilities should sum to 1
