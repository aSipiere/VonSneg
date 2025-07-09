from collections import defaultdict
from collections.abc import Callable
from functools import cache

from vonsneg.dice.roller import Roller
from vonsneg.rules.units import BaseUnit


def combine_distributions(
    dist_a: dict[int, float], dist_b: dict[int, float], combine_func: Callable[[int, int], int],
) -> dict[int, float]:
    result = defaultdict(float)
    for a_val, a_prob in dist_a.items():
        for b_val, b_prob in dist_b.items():
            combined = combine_func(a_val, b_val)
            result[combined] += float(a_prob) * float(b_prob)
    return dict(result)


class MeleeCombatSimulator:
    """Legacy class for backward compatibility.
    Use Turnip28MeleeSimulator for new code.
    """

    def __init__(
        self,
        attacker_models: int,
        attacker_attacks: int,
        attacker_to_hit: int,
        defender_to_save: int,
        defender_models: int,
        defender_attacks: int,
        defender_to_hit: int,
        attacker_save: int,
        attacker_wounds: int = 1,
        defender_wounds: int = 1,
    ):
        self.attacker = {
            "models": attacker_models,
            "attacks_per_model": attacker_attacks,
            "to_hit": attacker_to_hit,
            "to_save": attacker_save,
            "wounds_per_model": attacker_wounds,
        }
        self.defender = {
            "models": defender_models,
            "attacks_per_model": defender_attacks,
            "to_hit": defender_to_hit,
            "to_save": defender_to_save,
            "wounds_per_model": defender_wounds,
        }

    @classmethod
    def from_units(
        cls,
        attacker: BaseUnit,
        defender: BaseUnit,
        attacker_to_hit: int | None = None,
        defender_to_hit: int | None = None,
        attacker_to_save: int | None = None,
        defender_to_save: int | None = None,
    ) -> "MeleeCombatSimulator":
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
            defender_wounds=defender.stats.get("W", 1),
        )

    @cache
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
                self.defender["to_save"],
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
                    self.attacker["to_save"],
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
                    elif depth < max_depth:
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

        lines = ["```", "Combat Outcome:", bar, f"Win by ≥1: {win:.1%}", f"Lose by ≥1: {lose:.1%}", ""]

        lines.append("Wound Delta Distribution:")
        for net in sorted(result):
            if net == 0:
                continue  # skip draws
            outcome = f"Win by {net}" if net > 0 else f"Lose by {-net}"
            lines.append(f"{outcome:<12}: {result[net]:.2%}")

        lines.append("```")
        return "\n".join(lines)


class MeleeSimulator:
    """Simulates melee combat in Turnip28.
    Provides a consistent interface: can_engage, simulate, get_result, describe.
    Handles stand and shoot reactions before melee combat.
    """

    def __init__(self, attacker: BaseUnit, defender: BaseUnit):
        self.attacker = attacker
        self.defender = defender
        self._result_cache = None

    @cache
    def _wound_distribution(self, attacks: int, to_hit: int, to_save: int) -> dict[int, float]:
        """Calculate wound distribution for a given number of attacks."""
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

    def _can_stand_and_shoot(self) -> bool:
        """Check if the defender can stand and shoot back."""
        if hasattr(self.defender.weapon, "can_shoot"):
            return self.defender.weapon.can_shoot()
        return False

    def _calculate_stand_and_shoot_wounds(self) -> dict[int, float]:
        """Calculate the wound distribution from defender's stand and shoot."""
        if not self._can_stand_and_shoot():
            return {0: 1.0}

        # Calculate defender's inaccuracy (with Skirmish modifier)
        defender_inaccuracy = self.defender.inaccuracy()
        if "Skirmish" in self.attacker.traits:
            defender_inaccuracy += 2

        # Defender's stand and shoot
        defender_roller = Roller(num_dice=self.defender.models, target=defender_inaccuracy)
        defender_hit_dist = defender_roller.prob_dict()

        # Calculate defender's to-wound target with missile weapon modifier
        defender_to_wound_target = self.attacker.stats.get("V", 6)
        if hasattr(self.defender.weapon, "shooting_save_mod"):
            defender_to_wound_target += self.defender.weapon.shooting_save_mod

        defender_wound_dist = defaultdict(float)
        for hits, prob_hit in defender_hit_dist.items():
            if hits > 0:
                # The to_wound_target is actually the save target
                save_roller = Roller(num_dice=hits, target=defender_to_wound_target)
                save_dist = save_roller.prob_dict()
                for saves, prob_save in save_dist.items():
                    wounds = hits - saves  # Failed saves become wounds
                    defender_wound_dist[wounds] += prob_hit * prob_save
            else:
                defender_wound_dist[0] += prob_hit

        return dict(defender_wound_dist)

    def can_engage(self, **kwargs) -> bool:
        """Check if melee combat can proceed (both units must have models)."""
        return self.attacker.models > 0 and self.defender.models > 0

    def simulate(self, max_depth: int = 6, **kwargs) -> dict[int, float]:
        """Simulate melee combat with stand and shoot before combat begins.
        Returns a {wound_delta: probability} distribution (positive = attacker wins).
        Does not mutate input units.
        """
        if not self.can_engage():
            return {0: 1.0}

        # Handle stand and shoot first
        stand_and_shoot_dist = self._calculate_stand_and_shoot_wounds()

        # If no stand and shoot, proceed with normal melee
        if not self._can_stand_and_shoot():
            return self._simulate_melee_only(max_depth)

        # Combine stand and shoot with melee outcomes
        final_dist = defaultdict(float)

        for stand_wounds, stand_prob in stand_and_shoot_dist.items():
            # Calculate remaining attacker models after stand and shoot
            attacker_casualties = stand_wounds // self.attacker.stats.get("W", 1)
            remaining_attacker_models = max(self.attacker.models - attacker_casualties, 0)

            if remaining_attacker_models == 0:
                # Attacker wiped out by stand and shoot
                final_dist[-stand_wounds] += stand_prob
            else:
                # Proceed with melee using remaining models
                melee_dist = self._simulate_melee_only(max_depth, attacker_models=remaining_attacker_models)

                for melee_delta, melee_prob in melee_dist.items():
                    # Combine stand and shoot wounds with melee delta
                    # Positive melee_delta means attacker wins melee
                    # We need to account for the wounds already inflicted by stand and shoot
                    if melee_delta > 0:
                        # Attacker wins melee, but defender already inflicted stand_wounds
                        net_delta = melee_delta - stand_wounds
                        final_dist[net_delta] += stand_prob * melee_prob
                    else:
                        # Defender wins melee, plus the stand and shoot wounds
                        net_delta = melee_delta - stand_wounds
                        final_dist[net_delta] += stand_prob * melee_prob

        return dict(final_dist)

    def _simulate_melee_only(self, max_depth: int = 6, attacker_models: int = None) -> dict[int, float]:
        """Simulate melee combat without stand and shoot.
        Returns a {wound_delta: probability} distribution (positive = attacker wins).
        """
        if attacker_models is None:
            attacker_models = self.attacker.models

        def resolve_bout(attacker_models, defender_models, depth=0, weight=1.0):
            if attacker_models <= 0:
                return {-1: weight}
            if defender_models <= 0:
                return {1: weight}
            atk_attacks = attacker_models * self.attacker.stats["A"]
            atk_wound_dist = self._wound_distribution(
                atk_attacks,
                self.attacker.stats["I"],
                self.defender.stats["V"],
            )
            outcome_dist = defaultdict(float)
            for atk_wounds, p_hit in atk_wound_dist.items():
                def_remaining = max(defender_models - (atk_wounds // self.defender.stats.get("W", 1)), 0)
                def_attacks = def_remaining * self.defender.stats["A"]
                if def_attacks == 0:
                    outcome_dist[atk_wounds] += weight * p_hit
                    continue
                def_wound_dist = self._wound_distribution(
                    def_attacks,
                    self.defender.stats["I"],
                    self.attacker.stats["V"],
                )
                for def_wounds, p_def in def_wound_dist.items():
                    if weight * p_hit * p_def < 1e-12:
                        continue
                    total_prob = weight * p_hit * p_def
                    atk_remaining = max(attacker_models - (def_wounds // self.attacker.stats.get("W", 1)), 0)
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
                    elif depth < max_depth:
                        sub_result = resolve_bout(attacker_models, defender_models, depth + 1, total_prob)
                        if sub_result is not None:
                            for k, v in sub_result.items():
                                outcome_dist[k] += v
                    else:
                        outcome_dist[1] += total_prob * 0.5
                        outcome_dist[-1] += total_prob * 0.5
            return dict(outcome_dist)

        return dict(resolve_bout(attacker_models, self.defender.models))

    def get_result(self, **kwargs) -> dict[int, float]:
        """Get cached result or run simulation."""
        if self._result_cache is None:
            self._result_cache = self.simulate(**kwargs)
        return self._result_cache

    def describe(self) -> str:
        """Generate a human-readable description of the melee outcome."""
        result = self.get_result()
        win = sum(p for k, p in result.items() if k > 0)
        lose = sum(p for k, p in result.items() if k < 0)
        bar_width = 30
        win_bar = int(win * bar_width)
        lose_bar = int(lose * bar_width)
        bar = f"{'█' * win_bar}{'▓' * lose_bar}".ljust(bar_width)

        lines = [f"Melee: {self.attacker.name} → {self.defender.name}"]

        # Add stand and shoot information if applicable
        if self._can_stand_and_shoot():
            stand_and_shoot_dist = self._calculate_stand_and_shoot_wounds()
            expected_stand_wounds = sum(wounds * prob for wounds, prob in stand_and_shoot_dist.items())
            defender_inaccuracy = self.defender.inaccuracy()
            if "Skirmish" in self.attacker.traits:
                defender_inaccuracy += 2

            lines.extend(
                [
                    f"Stand and Shoot: {self.defender.name} → {self.attacker.name}",
                    f"Defender inaccuracy: {defender_inaccuracy}",
                    f"Expected stand and shoot wounds: {expected_stand_wounds:.2f}",
                    "",
                ],
            )

        lines.extend(
            [
                "Combat Outcome:",
                bar,
                f"Win by ≥1: {win:.1%}",
                f"Lose by ≥1: {lose:.1%}",
                "",
                "Wound Delta Distribution:",
            ],
        )

        for net in sorted(result):
            if net == 0:
                continue
            outcome = f"Win by {net}" if net > 0 else f"Lose by {-net}"
            lines.append(f"{outcome:<12}: {result[net]:.2%}")

        return "\n".join(lines)
