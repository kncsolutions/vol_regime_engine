from collections import Counter


class SystemicDiagnostics:

    # --------------------------------------------------
    # 1️⃣ Gamma Alignment
    # --------------------------------------------------

    def gamma_alignment(self, states):

        short = 0
        long = 0

        for s in states.values():
            regime = s.get("gamma_surface_regime")
            if regime == "SHORT_GAMMA":
                short += 1
            elif regime == "LONG_GAMMA":
                long += 1

        total = max(len(states), 1)
        return round(abs(short - long) / total, 3)

    # --------------------------------------------------
    # 2️⃣ Vol Expansion Breadth
    # --------------------------------------------------

    def vol_expansion_breadth(self, states):

        expanding = 0

        for s in states.values():
            accel = s.get("acceleration_probability", 0)
            surface = s.get("surface_shift_regime")

            if accel > 0.6 or surface == "VOL_EXPANSION":
                expanding += 1

        total = max(len(states), 1)
        return round(expanding / total, 3)

    # --------------------------------------------------
    # 3️⃣ Correlation Shock Index
    # --------------------------------------------------

    def correlation_shock(self, states):

        high_accel_regimes = []

        for s in states.values():
            if s.get("acceleration_probability", 0) > 0.7:
                high_accel_regimes.append(
                    s.get("gamma_surface_regime")
                )

        if not high_accel_regimes:
            return 0.0

        dominant = max(set(high_accel_regimes),
                       key=high_accel_regimes.count)

        alignment_ratio = (
            high_accel_regimes.count(dominant)
            / len(high_accel_regimes)
        )

        return round(alignment_ratio, 3)

    # --------------------------------------------------
    # 4️⃣ Regime Synchronization Score
    # --------------------------------------------------

    def regime_sync(self, states):

        regimes = [
            s.get("gamma_surface_regime")
            for s in states.values()
        ]

        if not regimes:
            return 0.0

        counter = Counter(regimes)
        dominant_count = counter.most_common(1)[0][1]

        return round(dominant_count / len(regimes), 3)

    # --------------------------------------------------
    # 5️⃣ Systemic Risk Index
    # --------------------------------------------------

    def systemic_risk_index(self, states):

        total = max(len(states), 1)

        avg_accel = 0
        short_gamma = 0
        low_persistence = 0
        instability_density = 0

        for s in states.values():

            accel = s.get("acceleration_probability", 0)
            confidence = s.get("regime_confidence", 0)
            persistence = confidence * (1 - 0.5 * accel)

            avg_accel += accel

            if s.get("gamma_surface_regime") == "SHORT_GAMMA":
                short_gamma += 1

            if persistence < 0.5:
                low_persistence += 1

            instability = s.get("instability_pockets")

            if isinstance(instability, list) and len(instability) > 0:
                instability_density += 1

        avg_accel /= total

        sri = (
            0.35 * avg_accel +
            0.25 * (short_gamma / total) +
            0.20 * (low_persistence / total) +
            0.20 * (instability_density / total)
        )

        return round(sri, 3)

    def cross_asset_flip_risk(self, states):

        total = max(len(states), 1)
        flip_sensitive = 0

        for s in states.values():

            spot = s.get("current_spot")
            flip = s.get("gamma_flip")
            accel = s.get("acceleration_probability", 0)

            if spot and flip:
                proximity = abs(spot - flip) / spot

                if proximity < 0.005 and accel > 0.5:
                    flip_sensitive += 1

        return round(flip_sensitive / total, 3)

    def early_crash_warning(self, states):

        sri = self.systemic_risk_index(states)
        gamma_align = self.gamma_alignment(states)
        vol_breadth = self.vol_expansion_breadth(states)
        flip_risk = self.cross_asset_flip_risk(states)
        corr_shock = self.correlation_shock(states)

        ecws = (
                0.30 * sri +
                0.25 * gamma_align +
                0.20 * vol_breadth +
                0.15 * flip_risk +
                0.10 * corr_shock
        )

        return round(ecws, 3)