from collections import defaultdict
from typing import Callable, Optional
from vonsneg.dice.roller import Roller
from vonsneg.rules.units import BaseUnit


def combine_distributions(dist_a: dict[int, float], dist_b: dict[int, float],
                          combine_func: Callable[[int, int], int]) -> dict[int, float]:
    result = defaultdict(float)
    for a_val, a_prob in dist_a.items():
        for b_val, b_prob in dist_b.items():
            combined = combine_func(a_val, b_val)
            result[combined] += float(a_prob) * float(b_prob)
    return dict(result)


class MeleeCombatSimulator:
    def __init__(self,
                 attacker_models: int,
                 attacker_attacks: int,
                 attacker_to_hit: int,
                 defender_to_save: int,
                 defender_models: int,
                 defender_attacks: int,
                 defender_to_hit: int,
                 attacker_save: int,
                 attacker_wounds: int = 1,
                 defender_wounds: int = 1):
        self.attacker = {
            "models": attacker_models,
            "attacks_per_model": attacker_attacks,
            "to_hit": attacker_to_hit,
            "to_save": attacker_save,
            "wounds_per_model": attacker_wounds
        }
        self.defender = {
            "models": defender_models,
            "attacks_per_model": defender_attacks,
            "to_hit": defender_to_hit,
            "to_save": defender_to_save,
            "wounds_per_model": defender_wounds
        }

    @classmethod
    def from_units(cls,
                   attacker: BaseUnit,
                   defender: BaseUnit,
                   attacker_to_hit: Optional[int] = None,
                   defender_to_hit: Optional[int] = None,
                   attacker_to_save: Optional[int] = None,
                   defender_to_save: Optional[int] = None) -> 'MeleeCombatSimulator':
        return cls(
            attacker_models=attacker.models,
            attacker_attacks=attacker.stats["A"],
            attacker_to_hit=attacker_to_hit or attacker.stats["I"],
            attacker_save=attacker_to_save or attacker.stats["V"],
            defender_models=defender.models,
            defender_attacks=defender.stats["A"],
            defender_to_hit=defender_to_hit or defender.stats["I"],
            defender_to_save=defender_to_save or defender.stats["V"],
            attacker_wounds=attacker.stats.get("W", 1),
            defender_wounds=defender.stats.get("W", 1)
        )

    def wound_distribution(self, attacks: int, to_hit: int, to_save: int) -> dict[int, float]:
        hit_dist = Roller(attacks, to_hit).prob_dict()
        wound_dist = defaultdict(float)
        for hits, p_hit in hit_dist.items():
            if hits == 0:
                wound_dist[0] += float(p_hit)
                continue
            save_dist = Roller(hits, to_save).prob_dict()
            for saves, p_save in save_dist.items():
                wounds = hits - saves
                wound_dist[wounds] += float(p_hit) * float(p_save)
        return dict(wound_dist)


    def model_loss_distribution(self, wound_dist: dict[int, float], wounds_per_model: int) -> dict[int, float]:
        model_dist = defaultdict(float)
        for wounds, prob in wound_dist.items():
            models_lost = wounds // wounds_per_model
            model_dist[models_lost] += prob
        return dict(model_dist)

    def result_distribution(self) -> dict[int, float]:
        atk_attacks = self.attacker["models"] * self.attacker["attacks_per_model"]
        def_attacks = self.defender["models"] * self.defender["attacks_per_model"]

        atk_wound_dist = self.wound_distribution(
            atk_attacks,
            self.attacker["to_hit"],
            self.defender["to_save"]
        )
        def_wound_dist = self.wound_distribution(
            def_attacks,
            self.defender["to_hit"],
            self.attacker["to_save"]
        )

        atk_model_dist = self.model_loss_distribution(atk_wound_dist, self.defender["wounds_per_model"])
        def_model_dist = self.model_loss_distribution(def_wound_dist, self.attacker["wounds_per_model"])

        return combine_distributions(
            atk_model_dist,
            def_model_dist,
            lambda atk_m, def_m: atk_m - def_m
        )

    def describe(self) -> str:
        result = self.result_distribution()
        lines = [f"Net models lost (attacker - defender):"]
        for net in sorted(result):
            outcome = "Draw" if net == 0 else (
                f"Win by {net}" if net > 0 else f"Lose by {-net}"
            )
            lines.append(f"{outcome:<12}: {result[net]:.2%}")
        return "\n".join(lines)
