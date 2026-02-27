"""
flow_impact_monitor.py

Production-grade Flow → Impact → Amplification Monitor.

Models:
    dS = k (Q_exog + GEX * dS)

Core equation:
    Amplification A = 1 / (1 - kG - k^2 G' Q)

Features:
- Liquidity-adjusted impact coefficient
- Linear and convexity instability metrics
- Amplification factor
- Bifurcation proximity estimate
- Stable numerical safeguards

Designed for vol_regime_engine integration.
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np


# ======================================================
# Data Structures
# ======================================================

@dataclass
class FlowImpactInputs:
    net_gex: float                 # Local aggregated GEX near spot
    gex_gradient: float            # dGEX/dS at spot
    exogenous_flow: float          # Live futures imbalance (contracts)
    daily_realized_vol: float      # e.g. 0.012 for 1.2%
    daily_futures_volume: float    # Total daily contracts
    fragility_score: float         # 0–100 systemic fragility
    baseline_impact_k: float       # Long-term calibrated impact coefficient


@dataclass
class FlowImpactConfig:
    liquidity_Y: float = 0.7
    min_denominator: float = 0.05
    max_amplification: float = 5.0
    instability_linear_threshold: float = 0.7
    instability_convexity_threshold: float = 1.0


# ======================================================
# Flow Impact Monitor
# ======================================================

class FlowImpactMonitor:

    def __init__(self, config: FlowImpactConfig = FlowImpactConfig()):
        self.config = config

    # --------------------------------------------------
    # Compute market impact coefficient k
    # --------------------------------------------------
    def _compute_k(self,
                   realized_vol: float,
                   futures_volume: float) -> float:

        if futures_volume <= 0:
            return 0.0

        return (
            self.config.liquidity_Y *
            realized_vol /
            futures_volume
        )

    # --------------------------------------------------
    # Linear instability metric
    # --------------------------------------------------
    def _compute_I1(self,
                    k: float,
                    net_gex: float) -> float:

        return k * net_gex

    # --------------------------------------------------
    # Convexity instability metric
    # --------------------------------------------------
    def _compute_I2(self,
                    k: float,
                    gex_gradient: float) -> float:

        return k * gex_gradient

    # --------------------------------------------------
    # Amplification factor
    # --------------------------------------------------
    def _compute_amplification(self,
                               k: float,
                               net_gex: float,
                               gex_gradient: float,
                               exog_flow: float,
                               fragility: float) -> float:

        denominator = (
            1
            - (k * net_gex)
            - (k ** 2 * gex_gradient * exog_flow)
        )

        # Numerical safeguard
        if abs(denominator) < self.config.min_denominator:
            denominator = np.sign(denominator) * self.config.min_denominator

        amplification = 1.0 / denominator

        # Fragility scaling
        amplification *= (1 + fragility / 100.0)

        # Clip extreme runaway values
        amplification = np.clip(
            amplification,
            -self.config.max_amplification,
            self.config.max_amplification
        )

        return amplification

    # --------------------------------------------------
    # Bifurcation proximity metric
    # --------------------------------------------------
    def _bifurcation_proximity(self,
                               k: float,
                               net_gex: float,
                               gex_gradient: float,
                               exog_flow: float) -> float:

        numerator = 1 - (k * net_gex)
        denominator = (k ** 2) * gex_gradient

        if abs(denominator) < 1e-12:
            return 0.0

        Q_critical = numerator / denominator

        if abs(Q_critical) < 1e-9:
            return 0.0

        return abs(exog_flow) / abs(Q_critical)

    # --------------------------------------------------
    # Public interface
    # --------------------------------------------------
    def evaluate(self,
                 inputs: FlowImpactInputs) -> Dict:

        # --- Liquidity coefficient ---
        k_current = self._compute_k(
            inputs.daily_realized_vol,
            inputs.daily_futures_volume
        )

        # --- Instability metrics ---
        I1 = self._compute_I1(k_current, inputs.net_gex)
        I2 = self._compute_I2(k_current, inputs.gex_gradient)

        # --- Amplification ---
        amplification = self._compute_amplification(
            k_current,
            inputs.net_gex,
            inputs.gex_gradient,
            inputs.exogenous_flow,
            inputs.fragility_score
        )

        # --- Bifurcation proximity ---
        bifurcation_ratio = self._bifurcation_proximity(
            k_current,
            inputs.net_gex,
            inputs.gex_gradient,
            inputs.exogenous_flow
        )

        # --- State classification ---
        if abs(I2) > self.config.instability_convexity_threshold:
            state = "CONVEXITY_RUNAWAY"
        elif abs(I1) > self.config.instability_linear_threshold:
            state = "LINEAR_FRAGILE"
        else:
            state = "STABLE"

        return {
            "impact_coefficient_k": k_current,
            "linear_instability_I1": I1,
            "convexity_instability_I2": I2,
            "amplification_factor": amplification,
            "bifurcation_proximity_ratio": bifurcation_ratio,
            "stability_state": state
        }