import numpy as np


def get_atm_iv(option_df, spot, iv_col="call_iv"):
    """
    Returns IV of strike closest to spot.
    """

    option_df = option_df.copy()

    option_df["distance"] = abs(option_df["strike"] - spot)

    atm_row = option_df.loc[
        option_df["distance"].idxmin()
    ]

    return atm_row[iv_col]