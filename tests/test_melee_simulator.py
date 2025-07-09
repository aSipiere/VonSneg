
from vonsneg.rules.melee import MeleeCombatSimulator


class DummyUnit:
    def __init__(self, name, models, A, I, V, W=1):
        self.name = name
        self.models = models
        self.stats = {"A": A, "I": I, "V": V, "W": W}


def test_simulator_direct():
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


def test_simulator_from_units():
    attacker = DummyUnit("Brutes", models=3, A=3, I=4, V=6, W=2)
    defender = DummyUnit("Fodder", models=10, A=1, I=5, V=5)

    sim = MeleeCombatSimulator.from_units(attacker, defender)
    dist = sim.result_distribution()

    assert isinstance(dist, dict)
    assert all(isinstance(k, int) and isinstance(v, float) for k, v in dist.items())
    assert 0 < sum(dist.values()) <= 1.0


def test_describe_output():
    attacker = DummyUnit("Brutes", models=3, A=3, I=4, V=6, W=2)
    defender = DummyUnit("Fodder", models=10, A=1, I=5, V=5)

    sim = MeleeCombatSimulator.from_units(attacker, defender)
    desc = sim.describe()

    assert isinstance(desc, str)
    assert "Net wounds dealt" in desc




class DummyUnit:
    def __init__(self, name, models, A, I, V, W=1):
        self.name = name
        self.models = models
        self.stats = {"A": A, "I": I, "V": V, "W": W}


def test_simulator_direct():
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


def test_simulator_from_units():
    attacker = DummyUnit("Brutes", models=3, A=3, I=4, V=6, W=2)
    defender = DummyUnit("Fodder", models=10, A=1, I=5, V=5)

    sim = MeleeCombatSimulator.from_units(attacker, defender)
    dist = sim.result_distribution()

    assert isinstance(dist, dict)
    assert all(isinstance(k, int) and isinstance(v, float) for k, v in dist.items())
    assert 0 < sum(dist.values()) <= 1.0


def test_describe_output():
    attacker = DummyUnit("Brutes", models=3, A=3, I=4, V=6, W=2)
    defender = DummyUnit("Fodder", models=10, A=1, I=5, V=5)

    sim = MeleeCombatSimulator.from_units(attacker, defender)
    desc = sim.describe()

    assert isinstance(desc, str)
    assert "Combat Outcome:" in desc
    assert "Wound Delta Distribution:" in desc
    assert "Win by ≥1" in desc
    assert "Lose by ≥1" in desc
