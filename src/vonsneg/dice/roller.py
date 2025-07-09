import random

from icepool import Pool, d6, d12


class Roller:
    def __init__(self, num_dice: int, target: int, modifier: int = 0):
        self.num_dice = num_dice
        self.target = target + modifier

    def simulate(self) -> int:
        if self.target < 7:
            # Normal rolling for target < 7
            results = [random.randint(1, 6) for _ in range(self.num_dice)]
            return sum(1 for roll in results if roll >= self.target)
        # For target >= 7, use d12 >= 12 (equivalent to roll 6 then 4+)
        results = [random.randint(1, 12) for _ in range(self.num_dice)]
        return sum(1 for roll in results if roll >= 12)

    def distribution(self):
        """Return a Population object (unnormalized frequencies)."""
        if self.num_dice == 0:
            # No dice: always 0 successes
            return {0: 1.0}
        if self.target < 7:
            # Normal distribution for target < 7
            success_die = (d6 >= self.target).map({True: 1, False: 0})
            return Pool([success_die] * self.num_dice).sum()
        # For target >= 7, use d12 >= 12 (equivalent to roll 6 then 4+)
        success_die = (d12 >= 12).map({True: 1, False: 0})
        return Pool([success_die] * self.num_dice).sum()

    def prob_dict(self) -> dict[int, float]:
        """Returns a dictionary of {successes: probability} for all outcomes."""
        if self.num_dice == 0:
            return {0: 1.0}
        dist = self.distribution()
        if isinstance(dist, dict):
            # Handle dict case (from two-stage process)
            return dist
        # Handle Population case (from normal process)
        return {k: dist.probability(k) for k in dist}
