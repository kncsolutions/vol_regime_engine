import json
import numpy as np
from pathlib import Path


class VolatilityDynamics:

    def __init__(self, base_dir="volatility_data"):
        self.base_dir = Path(base_dir)
        self.skew_dir = self.base_dir / "skew"
        self.surface_dir = self.base_dir / "surface"

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    def _get_latest_two_files(self, folder: Path):
        if not folder.exists():
            return None, None

        files = sorted(folder.glob("*.json"))

        if len(files) < 2:
            return None, None

        return files[-2], files[-1]

    def _load_json(self, file_path):
        with open(file_path, "r") as f:
            return json.load(f)

    # =========================================================
    # SKEW METRIC RECONSTRUCTION
    # =========================================================

    def _compute_skew_metrics(self, skew_json, spot):

        # Handle new structure
        if isinstance(skew_json, dict) and "points" in skew_json:
            points = skew_json["points"]
        elif isinstance(skew_json, list):
            points = skew_json
        else:
            return {}

        if not points:
            return {}

        strikes = np.array([row["strike"] for row in points])
        ivs = np.array([row["iv"] for row in points])

        # ATM IV
        distances = np.abs(strikes - spot)
        atm_iv = ivs[np.argmin(distances)]

        # Slope
        slope = (ivs[-1] - ivs[0]) / (strikes[-1] - strikes[0])

        # Curvature (quadratic)
        if len(strikes) >= 3:
            coeffs = np.polyfit(strikes, ivs, 2)
            curvature = coeffs[0]
        else:
            curvature = 0.0

        return {
            "atm_iv": float(atm_iv),
            "skew_slope": float(slope),
            "skew_curvature": float(curvature)
        }

    # =========================================================
    # PUBLIC: SKEW CHANGE FROM STORED FILES
    # =========================================================

    def compute_skew_change_from_store(self, underlying, session_type, spot):

        prev_file, curr_file = self._get_latest_two_files(self.skew_dir/underlying/session_type)

        if not prev_file or not curr_file:
            return None

        prev_json = self._load_json(prev_file)
        curr_json = self._load_json(curr_file)

        prev_metrics = self._compute_skew_metrics(prev_json, spot)
        curr_metrics = self._compute_skew_metrics(curr_json, spot)

        if not prev_metrics or not curr_metrics:
            return None

        return {
             "delta_atm_iv": curr_metrics["atm_iv"] - prev_metrics["atm_iv"],
            "delta_slope": curr_metrics["skew_slope"] - prev_metrics["skew_slope"],
            "delta_curvature": curr_metrics["skew_curvature"] - prev_metrics["skew_curvature"],
            "previous_file": prev_file.name,
            "current_file": curr_file.name
        }

    def _load_last_two_surfaces(self, folder: Path):

        base_dir = Path(folder)

        files = sorted(base_dir.glob("surface_*.json"))

        if len(files) < 2:
            return None, None

        import json

        with open(files[-2]) as f:
            prev_surface = json.load(f)

        with open(files[-1]) as f:
            curr_surface = json.load(f)

        return prev_surface, curr_surface

    # =========================================================
    # PUBLIC: SURFACE CHANGE FROM STORED FILES
    # =========================================================

    def compute_surface_change_from_store(self, underlying, session_type):

        prev_surface, curr_surface = self._load_last_two_surfaces(self.surface_dir / underlying / session_type)

        if not prev_surface or not curr_surface:
            return {}

        all_prev = []
        all_curr = []

        expiry_breakdown = {}

        for expiry in curr_surface.keys():

            if expiry not in prev_surface:
                continue

            prev_data = prev_surface[expiry].get("data", [])
            curr_data = curr_surface[expiry].get("data", [])

            if not prev_data or not curr_data:
                continue

            prev_ivs = np.array([row["iv"] for row in prev_data])
            curr_ivs = np.array([row["iv"] for row in curr_data])

            if len(prev_ivs) != len(curr_ivs):
                continue

            delta = curr_ivs - prev_ivs

            expiry_breakdown[expiry] = {
                "mean_iv_change": float(delta.mean()),
                "max_iv_change": float(delta.max()),
                "min_iv_change": float(delta.min())
            }

            all_prev.extend(prev_ivs)
            all_curr.extend(curr_ivs)

        if not all_prev:
            return {}

        all_prev = np.array(all_prev)
        all_curr = np.array(all_curr)

        parallel_shift = float((all_curr - all_prev).mean())

        return {
            "parallel_shift": parallel_shift,
            "expiry_breakdown": expiry_breakdown
        }

    # =========================================================
    # REGIME CLASSIFIERS
    # =========================================================

    def classify_surface_shift(self, surface_change):

        if not surface_change:
            return "NO_DATA"

        shift = surface_change.get("parallel_shift", 0)

        if shift > 0.01:
            return "VOL_EXPANSION"
        elif shift < -0.01:
            return "VOL_CRUSH"
        return "STABLE_SURFACE"


    def classify_skew_change(self, skew_change):

        if not skew_change:
            return "UNKNOWN"

        delta_slope = skew_change["delta_slope"]

        if delta_slope > 0.02:
            return "PANIC_BUILDING"

        if delta_slope < -0.02:
            return "HEDGE_UNWIND"

        return "STABLE_SKEW"

def map_shift_to_surface_score_label(surface_shift: str) -> str:
    """
    Maps shift-based surface regime
    to scoring dictionary labels safely.
    """

    if surface_shift is None:
        return "FLATTENING"

    mapping = {
        "VOL_EXPANSION": "BACK_STEEPENING",
        "VOL_CRUSH": "FLATTENING",
        "STABLE_SURFACE": "FLATTENING",
        "NO_DATA": "FLATTENING"
    }

    return mapping.get(surface_shift, "FLATTENING")
