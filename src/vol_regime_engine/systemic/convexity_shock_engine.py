"""
convexity_shock_engine.py

Production-grade Convexity Shock Engine.

Features:
- Gamma sign zone detection (above/below flip)
- ATR-based dynamic ATM window
- Nonlinear multi-step shock compounding
- Linear vs nonlinear hedge comparison
- Convexity ratio calculation
- Full crash acceleration condition
- Engine-ready structured output
"""

from dataclasses import dataclass
from typing import List, Dict
import numpy as np


# ======================================================
# Data Structures
# ======================================================

@dataclass
class StrikeGEX:
    strike: float
    net_gex: float


@dataclass
class ConvexityShockInputs:
    spot: float
    strikes: List[StrikeGEX]
    lot_size: int
    atr_points: float
    flip_level: float
    fragility_score: float

    daily_realized_vol: float
    daily_futures_volume: float
    baseline_impact_k: float

    shock_percent: float = 0.02
    atr_window_multiplier: float = 1.5
    nonlinear_steps: int = 2
    notional_shock_rupees: float = None  # NEW
    target_percent_move: float = None  # NEW


# ======================================================
# Engine
# ======================================================

class ConvexityShockEngine:

    # --------------------------------------------------
    # Dynamic ATM window based on ATR
    # --------------------------------------------------
    def _dynamic_window_pct(self, spot: float,
                            atr_points: float,
                            multiplier: float) -> float:

        if spot <= 0:
            return 0.01

        window_points = atr_points * multiplier
        return max(window_points / spot, 0.005)

    # --------------------------------------------------
    # Local GEX aggregation
    # --------------------------------------------------
    def _local_gex(self,
                   price: float,
                   strikes: List[StrikeGEX],
                   window_pct: float) -> float:

        lower = price * (1 - window_pct)
        upper = price * (1 + window_pct)

        values = [
            s.net_gex
            for s in strikes
            if lower <= s.strike <= upper
        ]

        return float(np.sum(values)) if values else 0.0

    # --------------------------------------------------
    # Gamma zone classification
    # --------------------------------------------------
    def _gamma_zone(self,
                    price: float,
                    flip_level: float) -> str:

        if price >= flip_level:
            return "DEALER_LONG_GAMMA_ZONE"
        return "DEALER_SHORT_GAMMA_ZONE"

    # --------------------------------------------------
    # Linear hedge estimate
    # --------------------------------------------------
    def _linear_hedge(self,
                      spot: float,
                      strikes: List[StrikeGEX],
                      window_pct: float,
                      shock_points: float) -> float:

        gex = self._local_gex(spot, strikes, window_pct)
        return gex * shock_points

    # --------------------------------------------------
    # Nonlinear multi-step compounding
    # --------------------------------------------------
    def _nonlinear_compound(self,
                            spot: float,
                            strikes: List[StrikeGEX],
                            window_pct: float,
                            shock_percent: float,
                            steps: int) -> float:

        if steps <= 0:
            return 0.0

        step_pct = shock_percent / steps
        current_price = spot
        total_hedge = 0.0

        for _ in range(steps):
            step_move = current_price * step_pct
            next_price = current_price + step_move

            gex = self._local_gex(next_price, strikes, window_pct)
            hedge = gex * step_move

            total_hedge += hedge
            current_price = next_price

        return total_hedge

    # --------------------------------------------------
    # Convexity ratio
    # --------------------------------------------------
    def _convexity_ratio(self,
                         linear: float,
                         nonlinear: float) -> float:

        if abs(linear) < 1e-9:
            return 0.0

        return abs(nonlinear) / abs(linear)

    # --------------------------------------------------
    # Liquidity Function
    # --------------------------------------------------

    def _compute_k(self, vol: float, volume: float) -> float:
        if volume <= 0:
            return 0.0
        Y = 0.7
        return Y * vol / volume

    def _dynamic_threshold(self,
                           base_threshold: float,
                           k_current: float,
                           k_baseline: float,
                           alpha: float = 1.5) -> float:

        if k_baseline <= 0:
            return base_threshold

        liquidity_ratio = k_current / k_baseline

        # Thin liquidity → lower threshold
        return base_threshold / (1 + alpha * liquidity_ratio)

    # --------------------------------------------------
    # Bifurcation Solver
    # --------------------------------------------------

    def _solve_bifurcation_threshold(self,
                                     k: float,
                                     net_gex: float,
                                     gex_gradient: float) -> Dict:

        # Avoid divide-by-zero
        if abs(gex_gradient) < 1e-12 or k == 0:
            return {
                "Q_critical": np.inf,
                "already_unstable": False
            }

        numerator = 1 - (k * net_gex)
        denominator = (k ** 2) * gex_gradient

        # If denominator ≈ 0, no convexity instability
        if abs(denominator) < 1e-12:
            return {
                "Q_critical": np.inf,
                "already_unstable": False
            }

        Q_critical = numerator / denominator

        already_unstable = numerator <= 0

        return {
            "Q_critical": Q_critical,
            "already_unstable": already_unstable
        }

    # --------------------------------------------------
    # GEX Gradient
    # --------------------------------------------------

    def _estimate_gradient(self,
                           spot: float,
                           strikes: List[StrikeGEX]) -> float:

        strikes_sorted = sorted(strikes, key=lambda x: x.strike)

        lower = max(
            (s for s in strikes_sorted if s.strike <= spot),
            key=lambda x: x.strike,
            default=None
        )

        upper = min(
            (s for s in strikes_sorted if s.strike > spot),
            key=lambda x: x.strike,
            default=None
        )

        if not lower or not upper:
            return 0.0

        dS = upper.strike - lower.strike
        if dS == 0:
            return 0.0

        return (upper.net_gex - lower.net_gex) / dS

    # --------------------------------------------------
    # Notional impact
    # --------------------------------------------------

    def _compute_notional_impact(self,
                                 notional_rupees: float,
                                 spot: float,
                                 lot_size: int,
                                 k: float,
                                 net_gex: float,
                                 gex_gradient: float) -> dict:

        if notional_rupees is None or notional_rupees <= 0:
            return {}

        # Convert ₹ to contracts
        contract_value = spot * lot_size
        contracts = notional_rupees / contract_value

        Q = contracts  # external flow in contracts

        # Linear denominator
        linear_denominator = 1 - (k * net_gex)

        if abs(linear_denominator) < 1e-6:
            linear_denominator = 1e-6

        # Full nonlinear denominator
        nonlinear_denominator = (
                1
                - (k * net_gex)
                - (k ** 2 * gex_gradient * Q)
        )

        if abs(nonlinear_denominator) < 1e-6:
            nonlinear_denominator = 1e-6

        # Compute price moves
        linear_move = (k * Q) / linear_denominator
        nonlinear_move = (k * Q) / nonlinear_denominator

        return {
            "notional_rupees": notional_rupees,
            "contracts_equivalent": contracts,
            "linear_move_points": linear_move,
            "nonlinear_move_points": nonlinear_move,
            "linear_percent_move": linear_move / spot,
            "nonlinear_percent_move": nonlinear_move / spot
        }

    def _solve_required_notional_for_move(self,
                                          target_percent_move: float,
                                          spot: float,
                                          lot_size: int,
                                          k: float,
                                          net_gex: float,
                                          gex_gradient: float) -> dict:

        if target_percent_move is None:
            return {}

        # Convert % move to points
        dS = spot * target_percent_move

        numerator = dS * (1 - k * net_gex)
        denominator = k + (dS * (k ** 2) * gex_gradient)

        if abs(denominator) < 1e-9:
            return {
                "error": "Denominator too small (near bifurcation)"
            }

        Q_required = numerator / denominator

        # Convert contracts → notional ₹
        contracts = Q_required
        contract_value = spot * lot_size
        notional_rupees = contracts * contract_value

        return {
            "target_percent_move": target_percent_move,
            "target_move_points": dS,
            "required_contracts": contracts,
            "required_notional_rupees": notional_rupees
        }

    # --------------------------------------------------
    # Public Interface
    # --------------------------------------------------
    def compute(self, inputs: ConvexityShockInputs) -> Dict:

        # --- Dynamic Window ---
        window_pct = self._dynamic_window_pct(
            inputs.spot,
            inputs.atr_points,
            inputs.atr_window_multiplier
        )

        shock_points = inputs.spot * inputs.shock_percent

        # --- Linear Hedge ---
        linear_total = self._linear_hedge(
            inputs.spot,
            inputs.strikes,
            window_pct,
            shock_points
        )

        # --- Nonlinear Hedge ---
        nonlinear_total = self._nonlinear_compound(
            inputs.spot,
            inputs.strikes,
            window_pct,
            inputs.shock_percent,
            inputs.nonlinear_steps
        )

        # --- Convexity Ratio ---
        ratio = self._convexity_ratio(
            linear_total,
            nonlinear_total
        )

        # --- Gamma Zones ---
        current_zone = self._gamma_zone(
            inputs.spot,
            inputs.flip_level
        )

        post_shock_zone = self._gamma_zone(
            inputs.spot + shock_points,
            inputs.flip_level
        )

        # --------------------------------------------------
        # FULL PRODUCTION CRASH CONDITION
        # --------------------------------------------------
        # --- Compute liquidity ---
        k_current = self._compute_k(
            inputs.daily_realized_vol,
            inputs.daily_futures_volume
        )

        dynamic_threshold = self._dynamic_threshold(
            base_threshold=1.5,
            k_current=k_current,
            k_baseline=inputs.baseline_impact_k
        )

        crash_acceleration = (
                ratio > dynamic_threshold and
                current_zone == "DEALER_SHORT_GAMMA_ZONE" and
                inputs.fragility_score > 70
        )


        # --- Local net GEX ---
        net_gex = self._local_gex(
            inputs.spot,
            inputs.strikes,
            window_pct
        )

        # --- Gradient ---
        gex_gradient = self._estimate_gradient(
            inputs.spot,
            inputs.strikes
        )

        # --- Solve bifurcation ---
        bifurcation = self._solve_bifurcation_threshold(
            k_current,
            net_gex,
            gex_gradient
        )

        current_flow = nonlinear_total  # or live order imbalance

        bifurcation_trigger = (
                abs(current_flow) >= abs(bifurcation["Q_critical"])
                and not bifurcation["already_unstable"]
        )

        # ---------------------------------------
        # Notional Impact Estimation
        # ---------------------------------------

        notional_impact = self._compute_notional_impact(
            notional_rupees=inputs.notional_shock_rupees,
            spot=inputs.spot,
            lot_size=inputs.lot_size,
            k=k_current,
            net_gex=net_gex,
            gex_gradient=gex_gradient
        )

        # ---------------------------------------
        # Reverse Solver: Required Notional for Target Move
        # ---------------------------------------

        required_notional = self._solve_required_notional_for_move(
            target_percent_move=inputs.target_percent_move,
            spot=inputs.spot,
            lot_size=inputs.lot_size,
            k=k_current,
            net_gex=net_gex,
            gex_gradient=gex_gradient
        )



        # --------------------------------------------------
        # Convert to contracts + notional
        # --------------------------------------------------
        contracts_linear = linear_total / inputs.lot_size
        contracts_nonlinear = nonlinear_total / inputs.lot_size

        notional_linear = contracts_linear * inputs.spot * inputs.lot_size
        notional_nonlinear = contracts_nonlinear * inputs.spot * inputs.lot_size

        return {
            "spot": inputs.spot,
            "shock_percent": inputs.shock_percent,
            "shock_points": shock_points,
            "dynamic_window_pct": window_pct,

            "gamma_zones": {
                "current_zone": current_zone,
                "post_shock_zone": post_shock_zone
            },

            "linear_hedge": {
                "delta_units": linear_total,
                "contracts": contracts_linear,
                "notional_rupees": notional_linear
            },

            "nonlinear_hedge": {
                "delta_units": nonlinear_total,
                "contracts": contracts_nonlinear,
                "notional_rupees": notional_nonlinear
            },

            "convexity_ratio": ratio,
            "convexity_acceleration": crash_acceleration,
            "bifurcation_analysis": {
                "net_gex": net_gex,
                "gex_gradient": gex_gradient,
                "impact_coefficient_k": k_current,
                "Q_critical": bifurcation["Q_critical"],
                "already_unstable": bifurcation["already_unstable"]
            },
            "notional_impact_estimate": notional_impact,
            "required_notional_for_target_move": required_notional
        }