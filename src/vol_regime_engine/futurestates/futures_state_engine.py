from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
@dataclass
class FuturesStateConfig:
    volume_window: int = 20
    high_volume_z: float = 1.0
    low_volume_z: float = -1.0
    persistence_bars: int = 3
    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 1.0
    gamma_threshold: float = 1e6   # adjust to your scale


class FuturesStateEngine:

    def __init__(self, config: FuturesStateConfig = FuturesStateConfig()):
        self.config = config
        self.prev_state = None
        self.last_confirmed_state = None
        self.persistence_count = 0
        self.transition_matrix = {}

    # --------------------------------------------------
    # Feature Engineering
    # --------------------------------------------------

    def compute_features(self, df: pd.DataFrame):

        df = df.copy()

        df["dP"] = df["close"].pct_change()
        df["dOI"] = df["open_interest"].pct_change()

        rolling_mean = df["volume"].rolling(self.config.volume_window).mean()
        rolling_std = df["volume"].rolling(self.config.volume_window).std()

        df["volume_z"] = (df["volume"] - rolling_mean) / rolling_std

        return df

    # --------------------------------------------------
    # Base State Classification
    # --------------------------------------------------

    def classify_base_state(self, dP, dOI):

        if dP > 0 and dOI > 0:
            return "LONG_BUILD"
        elif dP < 0 and dOI > 0:
            return "SHORT_BUILD"
        elif dP > 0 and dOI < 0:
            return "SHORT_COVER"
        elif dP < 0 and dOI < 0:
            return "LONG_LIQ"
        else:
            return "NEUTRAL"

    # --------------------------------------------------
    # Conviction Layer
    # --------------------------------------------------

    def add_conviction(self, base_state, volume_z):

        if volume_z > self.config.high_volume_z:
            return base_state + "_HIGH"
        elif volume_z < self.config.low_volume_z:
            return base_state + "_LOW"
        else:
            return base_state + "_NORMAL"

    # --------------------------------------------------
    # Persistence Filter
    # --------------------------------------------------

    def apply_persistence(self, current_state):

        # First observation
        if self.prev_state is None:
            self.prev_state = current_state
            self.persistence_count = 1
            return current_state

        # Same state continues
        if current_state == self.prev_state:
            self.persistence_count += 1
        else:
            self.persistence_count = 1

        # Only confirm after threshold
        if self.persistence_count >= self.config.persistence_bars:
            confirmed_state = current_state
        else:
            confirmed_state = self.prev_state

        self.prev_state = current_state

        return confirmed_state

    # --------------------------------------------------
    # Transition Tracking
    # --------------------------------------------------

    def update_transition_matrix(self, prev_state, current_state):

        if prev_state is None:
            return

        if prev_state not in self.transition_matrix:
            self.transition_matrix[prev_state] = {}

        if current_state not in self.transition_matrix[prev_state]:
            self.transition_matrix[prev_state][current_state] = 0

        self.transition_matrix[prev_state][current_state] += 1

    # --------------------------------------------------
    # Severity Score
    # --------------------------------------------------

    def compute_severity(self, dP, dOI, volume_z):

        return (
            abs(dP) ** self.config.alpha *
            abs(dOI) ** self.config.beta *
            abs(volume_z) ** self.config.gamma
        )

    # --------------------------------------------------
    # Combine Future Gamma
    # --------------------------------------------------

    def combine_futures_gamma(self, futures_state, gamma_regime):

        if gamma_regime == "MIXED_SURFACE":
            return futures_state + "_SURFACE_NEUTRAL"

        elif gamma_regime == "SHORT_GAMMA_SURFACE":

            if "LONG_BUILD" in futures_state:
                return futures_state + "_ACCELERATION_UP"

            if "SHORT_BUILD" in futures_state:
                return futures_state + "_ACCELERATION_DOWN"

        elif gamma_regime == "LONG_GAMMA_SURFACE":

            if "LONG_BUILD" in futures_state:
                return futures_state + "_MEAN_REVERT_RISK"

            if "SHORT_BUILD" in futures_state:
                return futures_state + "_SQUEEZE_RISK"

        return futures_state + "_FLOW_NEUTRAL"

    def compute_convexity_risk(self, severity, gamma_regime):

        if gamma_regime == "DEALER_SHORT_GAMMA":
            return severity * 2.0  # amplification factor
        return severity * 0.5

    # --------------------------------------------------
    # Public Interface
    # --------------------------------------------------

    def evaluate_latest(self, df: pd.DataFrame, gamma_regime):

        df = self.compute_features(df)
        latest = df.iloc[-1]

        base_state = self.classify_base_state(latest["dP"], latest["dOI"])
        state_with_conviction = self.add_conviction(base_state, latest["volume_z"])

        previous_confirmed_state = getattr(self, "last_confirmed_state", None)

        final_state = self.apply_persistence(state_with_conviction)

        # Track transitions on confirmed states only
        self.update_transition_matrix(previous_confirmed_state, final_state)

        self.last_confirmed_state = final_state

        severity = self.compute_severity(
            latest["dP"], latest["dOI"], latest["volume_z"]
        )
        composite_state = self.combine_futures_gamma(
            final_state,
            gamma_regime
        )

        convexity_risk = self.compute_convexity_risk(
            severity,
            gamma_regime
        )

        return {
            "future_base_state": base_state,
            "futures_final_state": final_state,
            "gamma_regime": gamma_regime,
            "composite_state": composite_state,
            "severity_score": float(severity),
            "convexity_risk": float(convexity_risk),
            "persistence": self.persistence_count,
            "transition_matrix": self.transition_matrix
        }