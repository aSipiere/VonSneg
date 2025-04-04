import random
from icepool import d6, Pool

class Roller:
    def __init__(self, num_dice: int, target: int, modifier: int = 0):
        self.num_dice = num_dice
        self.target = target + modifier

    def simulate(self) -> int:
        results = [random.randint(1, 6) for _ in range(self.num_dice)]
        return sum(1 for roll in results if roll >= self.target)

    def distribution(self):
        """Returns a Population object (unnormalized frequencies)."""
        success_die = (d6 >= self.target).map({True: 1, False: 0})
        return Pool([success_die] * self.num_dice).sum()

    def prob_dict(self) -> dict[int, float]:
        """Returns a dictionary of {successes: probability} for all outcomes."""
        dist = self.distribution()
        return {k: dist.probability(k) for k in dist}
