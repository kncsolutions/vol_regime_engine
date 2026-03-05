import numpy as np


def compute_convexity_ladder(df):

    # Required columns
    required = {"spot", "acceleration", "gamma_score"}

    if not required.issubset(df.columns):

        # Create empty targets if data missing
        df["target1"] = np.nan
        df["target2"] = np.nan
        return df

    pressure = df["acceleration"].fillna(0) * df["gamma_score"].fillna(0)

    df["target1"] = df["spot"] * (1 + pressure * 0.005)
    df["target2"] = df["spot"] * (1 + pressure * 0.01)

    return df