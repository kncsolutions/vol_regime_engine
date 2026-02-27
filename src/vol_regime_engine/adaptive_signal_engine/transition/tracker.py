class TransitionTracker:

    def __init__(self, regimes):
        self.regimes = regimes
        self.counts = {
            r: {r2: 1 for r2 in regimes}  # Laplace smoothing
            for r in regimes
        }

    def update(self, prev_regime, new_regime):
        self.counts[prev_regime][new_regime] += 1

    def get_matrix(self):
        matrix = {}
        for r in self.regimes:
            total = sum(self.counts[r].values())
            matrix[r] = {
                r2: self.counts[r][r2] / total
                for r2 in self.regimes
            }
        return matrix