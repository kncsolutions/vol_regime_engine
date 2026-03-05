from utils.safe_ops import safe_map


def compute_convexity_score(df):

    gamma_weight = {
        "short_gamma": 10,
        "flip_zone": 8,
        "long_gamma": 4
    }

    iv_weight = {
        "IV_CHEAP": 8,
        "IV_RICH": 5
    }

    df["gamma_score"] = safe_map(df["gamma_regime"], gamma_weight, 5)
    df["iv_score"] = safe_map(df["iv_vs_hv"], iv_weight, 5)

    df["acceleration"] = df.get("acceleration_probability", 0)

    df["convexity_score"] = (
        0.5 * df["acceleration"] * 10 +
        0.3 * df["gamma_score"] +
        0.2 * df["iv_score"]
    )

    return df