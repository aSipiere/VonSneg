from collections import defaultdict

from vonsneg.dice.roller import Roller
from vonsneg.rules.units import BaseUnit


class ShootingSimulator:
    """Simulates a shooting attack in Turnip28.
    Provides a consistent interface: can_engage, simulate, get_result, describe.
    Handles simultaneous stand and shoot reactions.
    """

    def __init__(self, attacker: BaseUnit, defender: BaseUnit):
        self.attacker = attacker
        self.defender = defender
        self._result_cache = None

    def can_engage(self, **kwargs) -> bool:
        """Check if the shooter can fire.

        :return: True if shooting can proceed
        """
        # Check if shooter can fire using the weapon's can_shoot attribute
        if hasattr(self.attacker.weapon, "can_shoot"):
            if not self.attacker.weapon.can_shoot():
                return False

        return True

    def _can_stand_and_shoot(self) -> bool:
        """Check if the defender can stand and shoot back."""
        if hasattr(self.defender.weapon, "can_shoot"):
            return self.defender.weapon.can_shoot()
        return False

    def simulate(self, **kwargs) -> dict[int, float]:
        """Simulate a shooting attack and return a {net_wounds: probability} distribution.
        If defender can stand and shoot, both sides fire simultaneously.
        Does not mutate input units.

        :return: Dictionary mapping net wounds to probabilities (positive = attacker wins)
        """
        if not self.can_engage():
            return {0: 1.0}

        # Calculate attacker's inaccuracy (with Skirmish modifier)
        attacker_inaccuracy = self.attacker.inaccuracy()
        if "Skirmish" in self.defender.traits:
            attacker_inaccuracy += 2

        # Attacker's shooting
        attacker_roller = Roller(num_dice=self.attacker.models, target=attacker_inaccuracy)
        attacker_hit_dist = attacker_roller.prob_dict()

        # Calculate attacker's to-wound target with missile weapon modifier
        attacker_to_wound_target = self.defender.stats.get("V", 6)
        if hasattr(self.attacker.weapon, "shooting_save_mod"):
            attacker_to_wound_target += self.attacker.weapon.shooting_save_mod

        attacker_wound_dist = defaultdict(float)
        for hits, prob_hit in attacker_hit_dist.items():
            if hits > 0:
                # The to_wound_target is actually the save target
                save_roller = Roller(num_dice=hits, target=attacker_to_wound_target)
                save_dist = save_roller.prob_dict()
                for saves, prob_save in save_dist.items():
                    wounds = hits - saves  # Failed saves become wounds
                    attacker_wound_dist[wounds] += prob_hit * prob_save
            else:
                attacker_wound_dist[0] += prob_hit

        # Check if defender can stand and shoot
        if self._can_stand_and_shoot():
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

            # Combine both distributions to get net wounds
            net_wound_dist = defaultdict(float)
            for atk_wounds, atk_prob in attacker_wound_dist.items():
                for def_wounds, def_prob in defender_wound_dist.items():
                    net_wounds = atk_wounds - def_wounds
                    net_wound_dist[net_wounds] += atk_prob * def_prob

            return dict(net_wound_dist)
        # No stand and shoot - just attacker's wounds
        return dict(attacker_wound_dist)

    def get_result(self, **kwargs) -> dict[int, float]:
        """Get cached result or run simulation."""
        if self._result_cache is None:
            self._result_cache = self.simulate(**kwargs)
        return self._result_cache

    def describe(self) -> str:
        """Generate a human-readable description of the shooting outcome."""
        result = self.get_result()

        # Calculate summary statistics
        if self._can_stand_and_shoot():
            # Net wounds (positive = attacker wins)
            expected_net_wounds = sum(wounds * prob for wounds, prob in result.items())
            attacker_wins = sum(prob for wounds, prob in result.items() if wounds > 0)
            defender_wins = sum(prob for wounds, prob in result.items() if wounds < 0)
            draw = sum(prob for wounds, prob in result.items() if wounds == 0)

            # Create visual bar
            bar_width = 30
            attacker_bar = int(attacker_wins * bar_width)
            defender_bar = int(defender_wins * bar_width)
            bar = f"{'█' * attacker_bar}{'▓' * defender_bar}".ljust(bar_width)

            # Show inaccuracy information
            attacker_inaccuracy = self.attacker.inaccuracy()
            if "Skirmish" in self.defender.traits:
                attacker_inaccuracy += 2
            defender_inaccuracy = self.defender.inaccuracy()
            if "Skirmish" in self.attacker.traits:
                defender_inaccuracy += 2

            lines = [
                f"Shooting: {self.attacker.name} ↔ {self.defender.name} (Stand and Shoot)",
                f"Attacker inaccuracy: {attacker_inaccuracy}",
                f"Defender inaccuracy: {defender_inaccuracy}",
                "Combat Outcome:",
                bar,
                f"Expected net wounds: {expected_net_wounds:.2f}",
                f"Attacker wins: {attacker_wins:.1%}",
                f"Defender wins: {defender_wins:.1%}",
                f"Draw: {draw:.1%}",
                "",
                "Net Wound Distribution:",
            ]

            for wounds in sorted(result.keys()):
                if result[wounds] > 0.001:
                    if wounds > 0:
                        lines.append(f"  Attacker wins by {wounds} wounds: {result[wounds]:.1%}")
                    elif wounds < 0:
                        lines.append(f"  Defender wins by {-wounds} wounds: {result[wounds]:.1%}")
                    else:
                        lines.append(f"  Draw: {result[wounds]:.1%}")
        else:
            # One-sided shooting
            expected_wounds = sum(wounds * prob for wounds, prob in result.items())
            expected_casualties = expected_wounds // self.defender.stats.get("W", 1)

            # Create simple bar for one-sided shooting
            bar_width = 30
            # Scale the bar based on expected wounds (cap at 100% for visual purposes)
            wound_percentage = min(expected_wounds / max(1, self.defender.models), 1.0)
            wound_bar = int(wound_percentage * bar_width)
            bar = f"{'█' * wound_bar}{'░' * (bar_width - wound_bar)}"

            # Show inaccuracy information
            attacker_inaccuracy = self.attacker.inaccuracy()
            if "Skirmish" in self.defender.traits:
                attacker_inaccuracy += 2

            lines = [
                f"Shooting: {self.attacker.name} → {self.defender.name}",
                f"Attacker inaccuracy: {attacker_inaccuracy}",
                "Expected Outcome:",
                bar,
                f"Expected wounds: {expected_wounds:.2f}",
                f"Expected casualties: {expected_casualties:.1f}",
                "",
                "Wound Distribution:",
            ]

            for wounds in sorted(result.keys()):
                if result[wounds] > 0.001:
                    casualties = wounds // self.defender.stats.get("W", 1)
                    lines.append(f"  {wounds} wounds ({casualties} casualties): {result[wounds]:.1%}")

        return "\n".join(lines)
