import numpy as np
import pandas as pd

def convexity_shock_percent(close, window=60):
    print(close)


    returns = np.log(close / close.shift(1))
    sigma = returns.rolling(window).std()

    acceleration = returns - returns.shift(1)

    shock_ratio = abs(acceleration) / sigma

    shock_percent = shock_ratio * sigma


    return shock_ratio.iloc[-1], shock_percent.iloc[-1]