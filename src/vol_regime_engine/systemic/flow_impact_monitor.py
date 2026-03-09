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
import pandas as pd


# ======================================================
# Data Structures
# ======================================================

@dataclass
class FlowImpactInputs:
    net_gex: float  # Local aggregated GEX near spot
    gex_gradient: float  # dGEX/dS at spot
    exogenous_flow: float  # Live futures imbalance (contracts)
    daily_realized_vol: float  # e.g. 0.012 for 1.2%
    daily_futures_volume: float  # Total daily contracts
    lot_size: float
    fut_baseline_ohlc: pd.DataFrame
    fut_tick_ohlc: pd.DataFrame
    fragility_score: float  # 0–100 systemic fragility
    baseline_impact_k: float  # Long-term calibrated impact coefficient


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

    def _infer_trade_side_numeric(self, df):

        df["price_diff"] = df["close"].diff()

        df["side"] = np.where(
            df["price_diff"] > 0, 1,
            np.where(df["price_diff"] < 0, -1, np.nan)
        )

        df["side"] = df["side"].ffill()

        return df

    def _compute_impact_k_bifurcation_proximity_ratio(self, df, window=500):

        df["mid"] = (df["low"] + df["high"]) / 2
        df = self._infer_trade_side_numeric(df)

        df["signed_volume"] = df["volume"] * df["side"]

        df["flow"] = df["signed_volume"].rolling(window).sum()
        df["dP"] = df["mid"].diff(window)

        df["k"] = df["dP"] / df["flow"]
        df["impact_flow"] = df["k"] * df["flow"]
        df["vol"] = df["mid"].pct_change().rolling(window).std()

        df["bpr"] = np.abs(df["impact_flow"]) / df["vol"]
        print(df[['k', "bpr", "volume"]])
        input('wait')



        return {"impact_coefficient_k":df["k"].iloc[-1],
                "bifurcation_proximity_ratio":df["bpr"].iloc[-1]}

    def compute_k_bpr(self, df, lot_size):

        df["price_diff"] = df["close"].diff()

        df["direction"] = np.sign(df["price_diff"])
        df["direction"] = df["direction"].replace(0, np.nan).ffill().fillna(0)

        df["OFI"] = df["volume"] * df["direction"] * lot_size

        df["OFI_roll"] = df["OFI"].rolling(30).sum()

        df["dP"] = df["close"].diff()

        valid = df.dropna()

        k = np.cov(valid["dP"], valid["OFI"])[0, 1] / np.var(valid["OFI"])

        sigma_p = valid["dP"].rolling(120).std().iloc[-1]
        sigma_p = max(sigma_p, 0.1)

        Q = valid["OFI_roll"].iloc[-1]

        BPR = abs(k * Q) / sigma_p

        return k, BPR

    # --------------------------------------------------
    # Linear instability metric
    # --------------------------------------------------
    def _compute_I1(self,
                    k: float,
                    net_gex: float) -> float:

        return abs(k * net_gex)

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
        # --- Bifurcation proximity ---
        if len(inputs.fut_tick_ohlc) > 0:
            # x= self._compute_impact_k_bifurcation_proximity_ratio(inputs.fut_tick_ohlc)
            # k_current = x["impact_coefficient_k"]
            # bifurcation_ratio = x["bifurcation_proximity_ratio"]
            k_current, bifurcation_ratio = self.compute_k_bpr(inputs.fut_tick_ohlc, inputs.lot_size)
            k_baseline, bifurcation_ratio_baseline = self.compute_k_bpr(inputs.fut_baseline_ohlc, inputs.lot_size)
        else:
            k_current = self._compute_k(
                inputs.daily_realized_vol,
                inputs.daily_futures_volume
            )

            bifurcation_ratio = self._bifurcation_proximity(
                k_current,
                inputs.net_gex,
                inputs.gex_gradient,
                inputs.exogenous_flow
            )
            k_baseline = 1e-7

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
            "stability_state": state,
            "impact_coefficient_k_baseline": k_baseline
        }
