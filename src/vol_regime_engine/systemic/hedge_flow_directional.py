"""
hedge_flow_directional.py

Computes directional Expected Dealer Hedge Flow
for +1% and -1% moves separately.

Designed for vol_regime_engine integration.
"""

from dataclasses import dataclass
from typing import List, Dict
import numpy as np


# ==========================================
# Data Structures
# ==========================================

@dataclass
class StrikeGEX:
    strike: float
    net_gex: float


@dataclass
class HedgeFlowInputs:
    spot: float
    strikes: List[StrikeGEX]
    lot_size: int
    percent_move: float = 0.01
    atm_window: float = 0.01  # % window around evaluation price


# ==========================================
# Core Estimator
# ==========================================

class DirectionalHedgeFlowEstimator:

    # --------------------------------------
    # Compute local GEX around arbitrary price
    # --------------------------------------
    def _local_gex(self, price: float,
                   strikes: List[StrikeGEX],
                   window: float) -> float:

        lower = price * (1 - window)
        upper = price * (1 + window)

        local = [
            s.net_gex
            for s in strikes
            if lower <= s.strike <= upper
        ]

        return np.sum(local) if local else 0.0

    # --------------------------------------
    # First-order slope estimate
    # --------------------------------------
    def _estimate_gradient(self,
                           spot: float,
                           strikes: List[StrikeGEX]) -> float:

        strikes_sorted = sorted(strikes, key=lambda x: x.strike)

        # Find nearest lower & upper strikes
        lower = max((s for s in strikes_sorted if s.strike <= spot),
                    key=lambda x: x.strike,
                    default=None)

        upper = min((s for s in strikes_sorted if s.strike > spot),
                    key=lambda x: x.strike,
                    default=None)

        if not lower or not upper:
            return 0.0

        dS = upper.strike - lower.strike
        if dS == 0:
            return 0.0

        return (upper.net_gex - lower.net_gex) / dS

    # --------------------------------------
    # Main function
    # --------------------------------------
    def compute(self, inputs: HedgeFlowInputs) -> Dict:

        move_points = inputs.spot * inputs.percent_move

        # Price levels
        up_price = inputs.spot + move_points
        down_price = inputs.spot - move_points

        # Local GEX at each level
        gex_up = self._local_gex(up_price,
                                 inputs.strikes,
                                 inputs.atm_window)

        gex_down = self._local_gex(down_price,
                                   inputs.strikes,
                                   inputs.atm_window)

        # First-order gradient
        gex_gradient = self._estimate_gradient(
            inputs.spot,
            inputs.strikes
        )

        # Hedge delta flows
        hedge_up = gex_up * move_points
        hedge_down = gex_down * (-move_points)

        # Convert to contracts
        contracts_up = hedge_up / inputs.lot_size
        contracts_down = hedge_down / inputs.lot_size

        # Notional
        notional_up = contracts_up * inputs.spot * inputs.lot_size
        notional_down = contracts_down * inputs.spot * inputs.lot_size

        return {
            "spot": inputs.spot,
            "move_points": move_points,
            "gex_gradient": gex_gradient,

            "upside": {
                "local_net_gex": gex_up,
                "hedge_delta_units": hedge_up,
                "futures_contracts": contracts_up,
                "notional_rupees": notional_up,
                "dealer_action": "BUY" if hedge_up > 0 else "SELL"
            },

            "downside": {
                "local_net_gex": gex_down,
                "hedge_delta_units": hedge_down,
                "futures_contracts": contracts_down,
                "notional_rupees": notional_down,
                "dealer_action": "BUY" if hedge_down > 0 else "SELL"
            }
        }