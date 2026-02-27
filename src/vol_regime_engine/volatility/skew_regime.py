import numpy as np


class SkewRegimeClassifier:

    def __init__(self, atm_window=0.02):
        self.atm_window = atm_window

    def compute_skew_metrics(self, option_df, spot, iv_col="iv"):
        """
        Computes:
        - downside IV
        - upside IV
        - ATM IV
        - slope
        - curvature
        """

        df = option_df.copy()
        df["moneyness"] = df["strike"] / spot

        # Define regions
        downside = df[df["moneyness"] < 0.98]
        upside = df[df["moneyness"] > 1.02]
        atm = df[
            (df["moneyness"] >= 0.98) &
            (df["moneyness"] <= 1.02)
        ]

        if atm.empty:
            return None

        atm_iv = atm[iv_col].mean()
        down_iv = downside[iv_col].mean()
        up_iv = upside[iv_col].mean()

        slope = down_iv - up_iv
        curvature = (down_iv + up_iv) - 2 * atm_iv

        return {
            "atm_iv": atm_iv,
            "downside_iv": down_iv,
            "upside_iv": up_iv,
            "slope": slope,
            "curvature": curvature
        }



    def classify(self, metrics):

        if metrics is None:
            return "UNKNOWN"

        slope = metrics["slope"]
        curvature = metrics["curvature"]

        # Panic skew
        if slope > 0.05:
            return "PANIC_SKEW"

        # Strong negative skew (normal equity regime)
        if slope > 0.02:
            return "NORMAL_NEGATIVE_SKEW"

        # Flat skew
        if abs(slope) < 0.01:
            return "FLAT_SKEW"

        # Inverted skew (upside IV bid)
        if slope < -0.01:
            return "INVERTED_SKEW"

        return "MILD_SKEW"

def map_skew_regime_to_score_label(skew_regime: str) -> str:
    """
    Maps skew classification output to scoring dictionary labels.
    Safe fallback included.
    """

    if skew_regime is None:
        return "FLAT"

    mapping = {
        "PANIC_SKEW": "EXTREME_PUT_HEAVY",
        "NORMAL_NEGATIVE_SKEW": "PUT_HEAVY",
        "MILD_SKEW": "PUT_HEAVY",
        "FLAT_SKEW": "FLAT",
        "INVERTED_SKEW": "CALL_HEAVY",
        "UNKNOWN": "FLAT"
    }

    return mapping.get(skew_regime, "FLAT")
