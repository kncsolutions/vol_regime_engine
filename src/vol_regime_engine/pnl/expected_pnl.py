import numpy as np


class ExpectedPnLModel:

    def __init__(self, capital: float = 1_000_000):
        self.capital = capital

    def expected_move(self, spot, iv, dte):
        """
        Expected 1-sigma move.
        """
        return spot * iv * np.sqrt(dte / 365)

    def vol_edge(self, iv, hv):
        """
        Volatility mispricing component.
        """
        return iv - hv

    def expected_theta_carry(self, total_theta):
        """
        Approx daily theta carry.
        """
        return total_theta

    def gamma_risk_adjustment(self, gamma_surface_regime):
        """
        Penalize short gamma environments.
        """
        if gamma_surface_regime == "SHORT_GAMMA_SURFACE":
            return -0.3
        return 0.1

    def estimate_short_vol(self, state):
        vol_spread = state["iv"] - state["hv"]
        carry = state["total_theta"]

        edge = vol_spread * 1000  # scale
        gamma_adj = self.gamma_risk_adjustment(
            state["gamma_surface_regime"]
        )

        expected = edge + carry + gamma_adj * 100

        return expected

    def estimate_long_vol(self, state):
        vol_spread = state["hv"] - state["iv"]

        instability_boost = 0
        if state["gamma_surface_regime"] == "SHORT_GAMMA_SURFACE":
            instability_boost = 200

        expected = vol_spread * 1000 + instability_boost

        return expected

    def evaluate(self, strategy_name: str, state: dict):

        if strategy_name == "Short Volatility":
            return self.estimate_short_vol(state)

        if strategy_name == "Long Volatility":
            return self.estimate_long_vol(state)

        return 0.0
