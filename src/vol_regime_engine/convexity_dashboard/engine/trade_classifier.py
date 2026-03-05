
def classify_trade(row):

    if row.gamma_regime == "SHORT_GAMMA":

        if row.bias == "trend_long":
            return "Call Buy"

        if row.bias == "trend_short":
            return "Put Buy"

    if row.gamma_regime == "FLIP_ZONE":
        return "Straddle"

    if row.gamma_regime == "LONG_GAMMA":
        return "Iron Condor"

    return "Watch"
