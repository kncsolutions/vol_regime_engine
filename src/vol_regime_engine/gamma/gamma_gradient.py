import numpy as np

def estimate_gradient(spot, strikes_df, window=0.05):

    lower = spot * (1 - window)
    upper = spot * (1 + window)

    df = strikes_df[
        (strikes_df["strike"] >= lower) &
        (strikes_df["strike"] <= upper)
    ]

    xs = df["strike"].values
    ys = df["net_gex"].values

    # remove NaNs
    mask = np.isfinite(xs) & np.isfinite(ys)
    xs = xs[mask]
    ys = ys[mask]

    if len(xs) < 3:
        return 0.0

    # center strikes for stability
    xs = xs - np.mean(xs)

    try:
        slope = np.polyfit(xs, ys, 1)[0]
    except np.linalg.LinAlgError:
        return 0.0

    return slope