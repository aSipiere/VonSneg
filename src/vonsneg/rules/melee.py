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

    from functools import lru_cache

    @lru_cache(maxsize=None)
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

    def result_distribution(self, max_depth=6):
        def resolve_bout(attacker_models, defender_models, depth=0, weight=1.0):
            if attacker_models <= 0:
                return {-1: weight}  # attacker wiped out
            if defender_models <= 0:
                return {1: weight}  # defender wiped out

            atk_attacks = attacker_models * self.attacker["attacks_per_model"]
            atk_wound_dist = self.wound_distribution(
                atk_attacks,
                self.attacker["to_hit"],
                self.defender["to_save"]
            )

            outcome_dist = defaultdict(float)

            for atk_wounds, p_hit in atk_wound_dist.items():
                def_remaining = max(defender_models - (atk_wounds // self.defender["wounds_per_model"]), 0)
                def_attacks = def_remaining * self.defender["attacks_per_model"]

                if def_attacks == 0:
                    outcome_dist[atk_wounds] += weight * p_hit
                    continue

                def_wound_dist = self.wound_distribution(
                    def_attacks,
                    self.defender["to_hit"],
                    self.attacker["to_save"]
                )

                for def_wounds, p_def in def_wound_dist.items():
                    if weight * p_hit * p_def < 1e-12:
                        continue
                    total_prob = weight * p_hit * p_def
                    atk_remaining = max(attacker_models - (def_wounds // self.attacker["wounds_per_model"]), 0)

                    if def_remaining <= 0:
                        outcome_dist[atk_wounds] += total_prob
                    elif atk_remaining <= 0:
                        outcome_dist[-def_wounds] += total_prob
                    elif atk_wounds > def_wounds:
                        delta = atk_wounds - def_wounds
                        outcome_dist[delta] += total_prob
                    elif def_wounds > atk_wounds:
                        delta = def_wounds - atk_wounds
                        outcome_dist[-delta] += total_prob
                    else:
                        if depth < max_depth:
                            sub_result = resolve_bout(attacker_models, defender_models, depth + 1, total_prob)
                            if sub_result is not None:
                                for k, v in sub_result.items():
                                    outcome_dist[k] += v
                        else:
                            outcome_dist[1] += total_prob * 0.5
                            outcome_dist[-1] += total_prob * 0.5

            return dict(outcome_dist)

        return dict(resolve_bout(self.attacker["models"], self.defender["models"]))

    def describe(self) -> str:
        result = self.result_distribution()
        win = sum(p for k, p in result.items() if k > 0)
        lose = sum(p for k, p in result.items() if k < 0)

        bar_width = 30
        win_bar = int(win * bar_width)
        lose_bar = int(lose * bar_width)
        bar = f"{'█' * win_bar}{'▓' * lose_bar}".ljust(bar_width)

        lines = ["```", "Combat Outcome:", bar,
                 f"Win by ≥1: {win:.1%}", f"Lose by ≥1: {lose:.1%}", ""]

        lines.append("Wound Delta Distribution:")
        for net in sorted(result):
            if net == 0:
                continue  # skip draws
            outcome = f"Win by {net}" if net > 0 else f"Lose by {-net}"
            lines.append(f"{outcome:<12}: {result[net]:.2%}")

        lines.append("```")
        return "\n".join(lines)
