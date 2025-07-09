"""Tests for melee combat simulator."""

from vonsneg.rules.melee import MeleeCombatSimulator


class DummyUnit:
    """Dummy unit class for testing purposes."""

    def __init__(self, name: str, models: int, attack: int, innacuraccy: int, vitality: int, wounds: int = 1) -> None:
        """Initialize a dummy unit for testing.

        Args:
            name: Unit name
            models: Number of models in unit
            attack: Attack stat (A)
            innacuraccy: innacuraccy stat (I)
            vitality: Vitality stat (V)
            wounds: Wounds per model (W)
        """
        self.name = name
        self.models = models
        self.stats = {"A": attack, "I": innacuraccy, "V": vitality, "W": wounds}


def test_simulator_direct() -> None:
    """Test direct simulator initialization and basic functionality."""
    sim = MeleeCombatSimulator(
        attacker_models=6,
        attacker_attacks=2,
        attacker_to_hit=4,
        attacker_save=6,
        defender_models=6,
        defender_attacks=2,
        defender_to_hit=4,
        defender_to_save=5,
        attacker_wounds=1,
        defender_wounds=1,
    )
    dist = sim.result_distribution()

    assert isinstance(dist, dict)
    assert 0 < sum(dist.values()) <= 1.0


def test_simulator_from_units() -> None:
    """Test simulator creation from unit objects."""
    attacker = DummyUnit("Brutes", models=3, attack=3, innacuraccy=4, vitality=6, wounds=2)
    defender = DummyUnit("Fodder", models=10, attack=1, innacuraccy=5, vitality=5)

    sim = MeleeCombatSimulator.from_units(attacker, defender)
    dist = sim.result_distribution()

    assert isinstance(dist, dict)
    assert all(isinstance(k, int) and isinstance(v, float) for k, v in dist.items())
    assert 0 < sum(dist.values()) <= 1.0


def test_describe_output() -> None:
    """Test the describe method output format."""
    attacker = DummyUnit("Brutes", models=3, attack=3, innacuraccy=4, vitality=6, wounds=2)
    defender = DummyUnit("Fodder", models=10, attack=1, innacuraccy=5, vitality=5)

    sim = MeleeCombatSimulator.from_units(attacker, defender)
    desc = sim.describe()

    assert isinstance(desc, str)
    assert "Combat Outcome:" in desc
    assert "Wound Delta Distribution:" in desc
    assert "Win by ≥1" in desc
    assert "Lose by ≥1" in desc
