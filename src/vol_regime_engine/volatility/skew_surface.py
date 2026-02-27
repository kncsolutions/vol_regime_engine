from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import numpy as np
SKEW_KEYS = {
    "atm_iv": "atm_iv",
    "slope": "skew_slope",
    "curvature": "skew_curvature"
}


class VolatilityStructureStore:

    def __init__(self, base_dir="volatility_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------
    # SKEW
    # ---------------------------

    def extract_skew(self, option_df, spot, iv_col="iv"):

        df = option_df[["strike", iv_col]].dropna().sort_values("strike")

        if df.empty:
            return {}

        # Distance to spot
        df["distance"] = (df["strike"] - spot).abs()

        # ATM IV
        atm_row = df.loc[df["distance"].idxmin()]
        atm_iv = float(atm_row[iv_col])

        # Linear slope
        slope = (
                        df.iloc[-1][iv_col] - df.iloc[0][iv_col]
                ) / (
                        df.iloc[-1]["strike"] - df.iloc[0]["strike"]
                )

        # Quadratic curvature
        x = df["strike"].values
        y = df[iv_col].values

        if len(df) >= 3:
            coeffs = np.polyfit(x, y, 2)
            curvature = float(coeffs[0])
        else:
            curvature = 0.0

        return {
            "atm_iv": atm_iv,
            "skew_slope": float(slope),
            "skew_curvature": curvature,
            "points": df[["strike", iv_col]].to_dict(orient="records")
        }

    def save_skew(self, expiry, underlying, session_type, skew_data):

        folder = self.base_dir / "skew" / underlying / session_type
        folder.mkdir(parents=True, exist_ok=True)

        if session_type == "intraday":
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        else:
            timestamp = datetime.utcnow().strftime("%Y%m%d")


        file_path = folder / f"{expiry}_{timestamp}.json"

        file_path.write_text(
            json.dumps(skew_data, indent=4),
            encoding="utf-8"
        )

        return file_path

    # ---------------------------
    # SURFACE
    # ---------------------------

    def extract_surface(self, option_chains, spot, iv_col="iv"):

        surface = {}

        for expiry, df in option_chains.items():

            if df.empty:
                continue

            df_clean = df[["strike", iv_col]].dropna()

            surface[expiry] = {
                "spot": spot,
                "data": df_clean.to_dict(orient="records"),
                "mean_iv": float(df_clean[iv_col].mean()),
                "std_iv": float(df_clean[iv_col].std())
            }

        return surface

    def save_surface(self, underlying, session_type, surface_data):

        folder = self.base_dir / "surface" / underlying /session_type
        folder.mkdir(parents=True, exist_ok=True)

        if session_type == "intraday":
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        else:
            timestamp = datetime.utcnow().strftime("%Y%m%d")

        file_path = folder / f"surface_{timestamp}.json"

        file_path.write_text(
            json.dumps(surface_data, indent=4),
            encoding="utf-8"
        )

        return file_path

