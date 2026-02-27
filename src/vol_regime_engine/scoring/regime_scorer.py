from dataclasses import dataclass
from typing import Dict
import numpy as np
from ..volatility.skew_regime import map_skew_regime_to_score_label
from ..volatility.surface_dynamics import map_shift_to_surface_score_label


# ---------------------------------------------------------
# Data Structure
# ---------------------------------------------------------

@dataclass
class RegimeScoreResult:
    gamma_score: float
    vol_score: float
    flow_score: float
    skew_surface_score: float
    cross_asset_score: float
    regime_score: float
    fragility_score: float
    transition_probability: float
    strategy_bias: str


# ---------------------------------------------------------
# Regime Scorer (Continuous Gamma Version)
# ---------------------------------------------------------

class RegimeScorer:

    def __init__(self,
                 w_gamma=0.30,
                 w_vol=0.20,
                 w_flow=0.20,
                 w_skew_surface=0.15,
                 w_cross=0.15):

        self.w_gamma = w_gamma
        self.w_vol = w_vol
        self.w_flow = w_flow
        self.w_skew_surface = w_skew_surface
        self.w_cross = w_cross

    # =====================================================
    # 1️⃣ Dynamic Gamma Score
    # =====================================================

    def compute_dynamic_gamma_score(self,
                                    option_chains,
                                    spot,
                                    gamma_flip_level,
                                    atr_pct,
                                    gex_scale):

        try:
            if not option_chains:
                return 0.0

            total_gex = sum(
                df["net_gex"].sum()
                for df in option_chains.values()
                if "net_gex" in df.columns
            )

        except Exception:
            return 0.0

        # Magnitude normalization (0 → 1)
        magnitude = np.tanh(abs(total_gex) / gex_scale)

        # Distance from flip (%)
        distance_pct = abs(spot - gamma_flip_level) / spot * 100

        if atr_pct == 0:
            stability = 0
        else:
            stability = 1 - np.exp(-distance_pct / atr_pct)

        sign = np.sign(total_gex)

        # Final continuous gamma score (-20 → +20)
        gamma_score = 20 * sign * magnitude * stability

        return gamma_score

    # =====================================================
    # 2️⃣ Other Component Scores
    # =====================================================

    def score_vol(self, iv: float, hv: float, vol_expanding: bool):

        if hv == 0:
            return 0

        z = (iv - hv) / hv

        if vol_expanding:
            return -20
        elif z > 0.25:
            return 15
        elif z > 0.05:
            return 5
        elif z < -0.05:
            return -10
        else:
            return 0

    def score_flow(self, futures_state: str, gamma_score: float):

        base_scores = {
            "LONG_BUILD": 10,
            "SHORT_COVER": 5,
            "NEUTRAL": 0,
            "LONG_LIQ": -5,
            "SHORT_BUILD": -10
        }

        score = base_scores.get(futures_state, 0)

        # Acceleration penalty if short gamma + long build
        if gamma_score < -5 and futures_state == "LONG_BUILD":
            score -= 10

        return score

    def score_skew_surface(self, skew_state: str, surface_state: str):

        skew_scores = {
            "EXTREME_PUT_HEAVY": -10,
            "PUT_HEAVY": -5,
            "FLAT": 0,
            "CALL_HEAVY": 5
        }

        surface_scores = {
            "FRONT_RICHENING": -5,
            "BACK_STEEPENING": -10,
            "FLATTENING": 5
        }

        return skew_scores.get(skew_state, 0) + surface_scores.get(surface_state, 0)

    def score_cross_asset(self, cross_asset_raw_score: float, max_score=25):
        return (cross_asset_raw_score / max_score) * 20

    # =====================================================
    # 3️⃣ Full Regime Computation
    # =====================================================

    def compute(self, state: Dict) -> RegimeScoreResult:

        # ---- Continuous Gamma Score ----
        G = self.compute_dynamic_gamma_score(
            option_chains=state["option_chains"],
            spot=state["spot"],
            gamma_flip_level=state["gamma_flip_level"],
            atr_pct=state["atr_pct"],
            gex_scale=state["gex_scale"]
        )

        V = self.score_vol(
            state["iv"],
            state["hv"],
            state.get("vol_expanding", False)
        )

        F = self.score_flow(
            state["futures_state"],
            G
        )

        mapped_skew = map_skew_regime_to_score_label(state["skew_state"])
        mapped_surface = map_shift_to_surface_score_label(state["surface_state"])

        S = self.score_skew_surface(
            mapped_skew,
            mapped_surface
        )

        X = self.score_cross_asset(
            state.get("cross_asset_raw_score", 0)
        )

        # Weighted regime score
        raw_score = (
            self.w_gamma * G +
            self.w_vol * V +
            self.w_flow * F +
            self.w_skew_surface * S -
            self.w_cross * X
        )

        regime_score = raw_score * 2  # scale to ~ -100 to +100

        # Fragility
        fragility_score = 100 - abs(regime_score)

        # Transition probability
        transition_probability = (fragility_score + X) / 200

        strategy_bias = self.map_strategy(regime_score)

        return RegimeScoreResult(
            gamma_score=G,
            vol_score=V,
            flow_score=F,
            skew_surface_score=S,
            cross_asset_score=X,
            regime_score=regime_score,
            fragility_score=fragility_score,
            transition_probability=transition_probability,
            strategy_bias=strategy_bias
        )

    # =====================================================
    # 4️⃣ Strategy Mapping
    # =====================================================

    def map_strategy(self, regime_score: float):

        if regime_score > 60:
            return "STRONG_MEAN_REVERSION_SHORT_VOL"
        elif 30 < regime_score <= 60:
            return "LIGHT_SHORT_VOL"
        elif -30 <= regime_score <= 30:
            return "NEUTRAL_OPTIONALITY_SMALL_SIZE"
        elif -60 <= regime_score < -30:
            return "LONG_GAMMA"
        else:
            return "LONG_CONVEXITY_TAIL_HEDGE"