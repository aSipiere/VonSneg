import random
from collections import defaultdict

from icepool import Pool, d6


class Roller:
    def __init__(self, num_dice: int, target: int, modifier: int = 0):
        self.num_dice = num_dice
        self.target = target + modifier

    def simulate(self) -> int:
        if self.target < 7:
            # Normal rolling for target < 7
            results = [random.randint(1, 6) for _ in range(self.num_dice)]
            return sum(1 for roll in results if roll >= self.target)
        # Two-stage process for target >= 7
        # Stage 1: Roll 6s
        stage1_results = [random.randint(1, 6) for _ in range(self.num_dice)]
        sixes = sum(1 for roll in stage1_results if roll == 6)

        if sixes == 0:
            return 0

        # Stage 2: For each 6 rolled, roll again with target 4
        stage2_results = [random.randint(1, 6) for _ in range(sixes)]
        return sum(1 for roll in stage2_results if roll >= 4)

    def distribution(self):
        """Returns a Population object (unnormalized frequencies)."""
        if self.num_dice == 0:
            # No dice: always 0 successes
            return {0: 1.0}
        if self.target < 7:
            # Normal distribution for target < 7
            success_die = (d6 >= self.target).map({True: 1, False: 0})
            return Pool([success_die] * self.num_dice).sum()
        # Two-stage process for target >= 7
        # Stage 1: Roll 6s
        stage1_die = (d6 == 6).map({True: 1, False: 0})
        stage1_dist = Pool([stage1_die] * self.num_dice).sum()
        # Stage 2: For each 6, roll 4+
        stage2_die = (d6 >= 4).map({True: 1, False: 0})

        # Build the final distribution manually
        final_dist = defaultdict(float)
        for sixes, p_sixes in stage1_dist.items():
            if sixes == 0:
                # No sixes means 0 successes
                final_dist[0] += p_sixes
            else:
                # Sixes means roll stage2
                stage2_dist = Pool([stage2_die] * sixes).sum()
                for successes, p_success in stage2_dist.items():
                    final_dist[successes] += p_sixes * p_success

        # Normalize the distribution to sum to 1.0
        total_prob = sum(final_dist.values())
        if total_prob > 0:
            normalized_dist = {k: v / total_prob for k, v in final_dist.items()}
            return normalized_dist
        # All weights are zero - return 0 with probability 1
        return {0: 1.0}

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
