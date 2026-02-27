import pandas as pd


def instability_intensity(state: dict):
    """
    Returns instability intensity between 0 and 1.
    Handles list or DataFrame input.
    """

    pockets = state.get("instability_pockets")
    spot = state.get("spot")

    if spot is None or pockets is None:
        return 0.0

    # ---- Case 1: DataFrame ----
    if isinstance(pockets, pd.DataFrame):

        if pockets.empty:
            return 0.0

        # Expect column named 'strike' (adjust if different)
        if "strike" not in pockets.columns:
            return 0.0

        distances = abs(pockets["strike"] - spot)

        nearest = distances.min()

    # ---- Case 2: List / Iterable ----
    else:
        try:
            distances = [abs(level - spot) for level in pockets]
            if not distances:
                return 0.0
            nearest = min(distances)
        except Exception:
            return 0.0

    normalized = nearest / spot

    if normalized < 0.005:
        return 1.0
    elif normalized < 0.01:
        return 0.5

    return 0.0