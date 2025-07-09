"""Tests for dice rolling mechanics."""

from fractions import Fraction

import pytest

from vonsneg.dice.roller import Roller

# Constants for test values
MAX_DICE = 10
MIN_EXPECTED = 2.5
MAX_EXPECTED = 4.0


def test_simulate_range() -> None:
    """Test that simulation results are within expected range."""
    roller = Roller(num_dice=MAX_DICE, target=4)
    result = roller.simulate()
    assert 0 <= result <= MAX_DICE


def test_prob_dict_structure() -> None:
    """Test that probability dictionary has correct structure."""
    roller = Roller(num_dice=5, target=4)
    prob_dict = roller.prob_dict()

    assert isinstance(prob_dict, dict)
    assert all(isinstance(k, int) for k in prob_dict)
    assert all(isinstance(v, (float, Fraction)) for v in prob_dict.values())


def test_distribution_total_probability() -> None:
    """Test that probability distribution sums to 1.0."""
    roller = Roller(num_dice=5, target=4)
    total_prob = sum(roller.prob_dict().values())
    assert pytest.approx(total_prob, abs=1e-6) == 1.0


def test_expected_value_accuracy() -> None:
    """Test that expected value is within reasonable bounds."""
    roller = Roller(num_dice=6, target=4)
    dist = roller.distribution()
    expected = dist.mean()
    assert MIN_EXPECTED < expected < MAX_EXPECTED


def test_modifier_adjusts_target() -> None:
    """Test that modifiers correctly adjust target difficulty."""
    base_mean = Roller(6, target=4, modifier=0).distribution().mean()
    harder_mean = Roller(6, target=4, modifier=1).distribution().mean()
    easier_mean = Roller(6, target=4, modifier=-1).distribution().mean()

    assert base_mean > harder_mean
    assert base_mean < easier_mean


def test_extreme_modifier_results() -> None:
    """Test extreme modifier scenarios."""
    # Two-stage process for targets >= 7 (roll 6s, then 4+ for each 6)
    roller = Roller(num_dice=MAX_DICE, target=6, modifier=1)
    prob_dict = roller.prob_dict()
    # Should have some probability of success due to two-stage process
    assert prob_dict.get(0, 0.0) < 1.0
    assert sum(prob_dict.values()) == pytest.approx(1.0, abs=1e-6)

    # Always succeed (1+)
    roller = Roller(num_dice=MAX_DICE, target=2, modifier=-1)
    prob_dict = roller.prob_dict()
    assert pytest.approx(prob_dict.get(MAX_DICE, 0.0), abs=1e-6) == 1.0
