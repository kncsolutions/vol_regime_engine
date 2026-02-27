import numpy as np


class StateChangeAnalyzer:

    def __init__(self, numeric_thresholds=None):

        # default thresholds
        self.thresholds = numeric_thresholds or {
            "iv": 0.005,
            "hv": 0.005,
            "total_gex": 1e6,
            "total_theta": 1e4,
            "intraday_stress_score": 2.0
        }

    # --------------------------------------------------
    # Detect categorical state changes
    # --------------------------------------------------

    def detect_categorical_changes(self, prev_state, curr_state):

        categorical_fields = [
            "gamma_surface_regime",
            "iv_vs_hv",
            "skew_regime",
            "surface_shift_regime",
            "strategy_name"
        ]

        changes = {}

        for field in categorical_fields:
            prev = prev_state.get(field)
            curr = curr_state.get(field)

            if prev != curr:
                changes[field] = {
                    "previous": prev,
                    "current": curr
                }

        return changes

    # --------------------------------------------------
    # Detect numeric drifts
    # --------------------------------------------------

    def detect_numeric_changes(self, prev_state, curr_state):

        numeric_fields = [
            "iv",
            "hv",
            "total_gex",
            "total_theta",
            "intraday_stress_score"
        ]

        changes = {}

        for field in numeric_fields:

            prev = prev_state.get(field)
            curr = curr_state.get(field)

            if prev is None or curr is None:
                continue

            delta = curr - prev
            threshold = self.thresholds.get(field, 0)

            if abs(delta) > threshold:
                changes[field] = {
                    "previous": prev,
                    "current": curr,
                    "delta": delta
                }

        return changes

    # --------------------------------------------------
    # Master method
    # --------------------------------------------------

    def analyze(self, df):

        if len(df) < 2:
            return {}

        prev_state = df.iloc[-2].to_dict()
        curr_state = df.iloc[-1].to_dict()

        return {
            "categorical_changes": self.detect_categorical_changes(
                prev_state, curr_state
            ),
            "numeric_changes": self.detect_numeric_changes(
                prev_state, curr_state
            )
        }
