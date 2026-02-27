import numpy as np
import pandas as pd

class AccelerationProbabilityModel:

    def compute(self, state):

        net_gex = state.get("net_gex", 0)
        flip = state.get("gamma_flip")
        spot = state.get("current_spot")
        surface = state.get("surface_change", {})
        skew = state.get("skew_change", {})

        score = 0

        # 1️⃣ Short gamma boost
        if net_gex < 0:
            score += 0.3

        # 2️⃣ Near flip boost
        if flip and spot:
            distance = abs(spot - flip) / spot
            if distance < 0.005:
                score += 0.2

        # 3️⃣ Surface expansion
        if isinstance(surface, dict):
            if surface.get("parallel_shift", 0) > 0:
                score += 0.2

        # 4️⃣ Skew steepening
        if isinstance(skew, dict):
            if skew.get("delta_slope", 0) > 0:
                score += 0.2

        # 5️⃣ Instability present


        instability = state.get("instability_pockets")

        inst_count = 0

        if instability is not None:

            # Case 1 — DataFrame
            if isinstance(instability, pd.DataFrame):
                if not instability.empty:
                    inst_count = len(instability)

            # Case 2 — List
            elif isinstance(instability, list):
                inst_count = len(instability)

        # Apply contribution
        if inst_count > 0:
            score += 0.1

        return round(min(score, 1.0), 3)