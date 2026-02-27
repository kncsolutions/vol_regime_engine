import numpy as np

def calculate_hv(spot_df, window):
    spot_df = spot_df.sort_values("date")
    spot_df["log_ret"] = np.log(
        spot_df["close"] / spot_df["close"].shift(1)
    )
    return (
        spot_df["log_ret"]
        .rolling(window)
        .std()
        * np.sqrt(252)
    )

def get_current_hv(spot_df, window=20):
    hv_series = calculate_hv(spot_df, window)
    return hv_series.iloc[-1] * 100
