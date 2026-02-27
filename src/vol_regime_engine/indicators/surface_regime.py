# vol_regime_engine/indicators/surface_regime.py

import numpy as np
import pandas as pd
from datetime import datetime


class MultiExpirySurfaceDetector:

    def __init__(self,
                 slope_threshold=0.3,
                 curvature_threshold=0.1,
                 front_pressure_threshold=0.3):

        self.slope_threshold = slope_threshold
        self.curvature_threshold = curvature_threshold
        self.front_pressure_threshold = front_pressure_threshold

    # ---------------------------------------------------------
    # Extract ATM IV per expiry
    # ---------------------------------------------------------

    def _extract_atm_iv(self, option_chains, spot):
        """
        Returns:
            times (list of T in years)
            ivs (list of ATM IV)
        """

        times = []
        ivs = []

        today = datetime.utcnow()

        for expiry, df in option_chains.items():

            if "strike" not in df.columns or "iv" not in df.columns:
                continue

            # Convert expiry to datetime
            expiry_dt = pd.to_datetime(expiry)

            # Time to expiry in years
            t = (expiry_dt - today).days / 365.0
            if t <= 0:
                continue

            # Find ATM strike
            df = df.copy()
            df["distance"] = abs(df["strike"] - spot)

            atm_row = df.loc[df["distance"].idxmin()]

            atm_iv = atm_row["iv"]

            if pd.isna(atm_iv):
                continue

            times.append(t)
            ivs.append(atm_iv)

        # Sort by time
        if len(times) < 3:
            return None, None

        times, ivs = zip(*sorted(zip(times, ivs)))

        return np.array(times), np.array(ivs)

    # ---------------------------------------------------------
    # Fit quadratic
    # ---------------------------------------------------------

    def _fit_surface(self, times, ivs):
        coeffs = np.polyfit(times, ivs, 2)
        a, b, c = coeffs
        return b, c

    # ---------------------------------------------------------
    # Public Detect Method
    # ---------------------------------------------------------

    def detect(self,
               current_option_chains,
               previous_option_chains,
               spot):

        times_now, iv_now = self._extract_atm_iv(
            current_option_chains,
            spot
        )

        times_prev, iv_prev = self._extract_atm_iv(
            previous_option_chains,
            spot
        )

        if times_now is None or times_prev is None:
            return "UNKNOWN"

        if len(times_now) < 3 or len(times_prev) < 3:
            return "UNKNOWN"

        b_now, c_now = self._fit_surface(times_now, iv_now)
        b_prev, c_prev = self._fit_surface(times_prev, iv_prev)

        slope_change = b_now - b_prev
        curvature_change = c_now - c_prev

        front_change = iv_now[0] - iv_prev[0]
        back_change = iv_now[-1] - iv_prev[-1]

        # -----------------------------------------------------
        # Classification
        # -----------------------------------------------------

        if front_change > self.front_pressure_threshold and back_change <= 0:
            return "FRONT_RICHENING"

        if slope_change > self.slope_threshold:
            return "BACK_STEEPENING"

        if slope_change < -self.slope_threshold:
            return "FLATTENING"

        if abs(curvature_change) > self.curvature_threshold:
            return "CURVATURE_SHIFT"

        if abs(front_change - back_change) < 0.1:
            return "PARALLEL_SHIFT"

        return "FLATTENING"