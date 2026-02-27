# vol_regime_engine/scaling/simple_gex_scale.py

import numpy as np


class SimpleGEXScale:

    def __init__(self,
                 alpha: float = 2.0,
                 min_scale: float = 1e8,
                 smoothing: float = 0.2):
        """
        Parameters:
        alpha : multiplier to expand current |GEX|
        min_scale : floor to prevent zero division
        smoothing : EMA smoothing factor (0 disables smoothing)
        """
        self.alpha = alpha
        self.min_scale = min_scale
        self.smoothing = smoothing
        self._previous_scale = None

    # ---------------------------------------------------------
    # Compute total GEX from current option chains
    # ---------------------------------------------------------

    @staticmethod
    def compute_total_gex(option_chains):

        try:
            total_gex = sum(
                df["net_gex"].sum()
                for df in option_chains.values()
                if "net_gex" in df.columns
            )
            return float(total_gex)
        except Exception:
            return 0.0

    # ---------------------------------------------------------
    # Dynamic scale based only on current snapshot
    # ---------------------------------------------------------

    def compute_scale(self, option_chains):

        total_gex = self.compute_total_gex(option_chains)

        base_scale = self.alpha * abs(total_gex)

        scale = max(base_scale, self.min_scale)

        # Optional smoothing to avoid sudden jumps
        if self.smoothing > 0:
            if self._previous_scale is None:
                self._previous_scale = scale
            else:
                scale = (
                    self.smoothing * scale
                    + (1 - self.smoothing) * self._previous_scale
                )
                self._previous_scale = scale

        return scale