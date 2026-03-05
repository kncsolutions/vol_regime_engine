from ..engine.convexity_ladder import compute_convexity_ladder
from ..engine.dealer_simulator import dealer_pressure, simulate_hedging


def convexity_score(df):

    gamma_weight = {
        "short_gamma": 10,
        "flip_zone": 8,
        "long_gamma": 4
    }

    iv_weight = {
        "IV_CHEAP": 8,
        "IV_RICH": 5
    }

    print("DF columns:", df.columns)
    print(df.head())

    df["gamma_score"] = df.gamma_regime.map(gamma_weight).fillna(5)
    df["iv_score"] = df.iv_hv.map(iv_weight).fillna(5)

    df["convexity_score"] = (
        0.5 * df.acceleration.fillna(0) * 10
        + 0.3 * df.gamma_score
        + 0.2 * df.iv_score
    )

    # Convexity ladder
    df = compute_convexity_ladder(df)

    # Dealer pressure metric
    df["dealer_pressure"] = df["gamma_score"] * df["acceleration"]

    def compute_gamma_flip(df):

        # simple proxy for instability threshold
        df["gamma_flip"] = (
                df["target1"] * 0.5 +
                df["target2"] * 0.5
        )

        return df

    df = compute_gamma_flip(df)
    df["flip_risk"] = abs(df["spot"] - df["gamma_flip"])

    # Sort opportunities
    df = df.sort_values("convexity_score", ascending=False)
    # normalize dealer pressure
    if "dealer_pressure" in df.columns:
        dp = df["dealer_pressure"].fillna(0)
        dp_norm = dp / (dp.max() if dp.max() != 0 else 1)
    else:
        dp_norm = 0

    # normalize gamma instability
    gamma_norm = df["gamma_score"] / 10

    # normalize IV signal
    iv_norm = df["iv_score"] / 10

    # acceleration already 0-1
    accel = df["acceleration"].fillna(0)

    df["shock_score"] = (
            0.4 * accel
            + 0.3 * gamma_norm
            + 0.2 * dp_norm
            + 0.1 * iv_norm
    )

    # ------------------------------------------------
    # Run hedging simulation ONLY for top opportunities
    # ------------------------------------------------

    simulations = {}

    top_symbols = df.head(5)

    for _, row in top_symbols.iterrows():

        spot = row.get("spot", None)

        if spot is None:
            continue

        gamma_exposure = row["dealer_pressure"] * 10000

        prices = simulate_hedging(
            spot=spot,
            gamma_exposure=gamma_exposure,
            steps=30
        )

        simulations[row["symbol"]] = prices

    return df, simulations
