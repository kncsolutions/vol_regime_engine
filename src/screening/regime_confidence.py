import numpy as np


class RegimeConfidenceModel:

    def compute(self, state, intraday_metrics=None):

        regime = state.get("gamma_surface_regime")
        half_life = state.get("gamma_half_life", {}).get(regime)
        stress = state.get("intraday_stress_score", 0)
        instability = state.get("instability_pockets")

        score = 0.0

        # 1️⃣ Half-life contribution
        if half_life and half_life != float("inf"):
            score += min(half_life / 10, 1.0) * 0.4
        elif half_life == float("inf"):
            score += 0.4

        # 2️⃣ Stress penalty
        stress_penalty = min(stress / 5, 1.0)
        score += (1 - stress_penalty) * 0.3

        # 3️⃣ Instability penalty
        if instability is not None:
            if hasattr(instability, "empty"):
                inst_count = 0 if instability.empty else len(instability)
            elif isinstance(instability, list):
                inst_count = len(instability)
            else:
                inst_count = 0
        else:
            inst_count = 0

        score += max(0, 1 - inst_count / 5) * 0.3

        return round(score, 3)