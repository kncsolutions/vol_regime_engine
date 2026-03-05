
def classify_market_state(accel):

    if accel < 0.3:
        return "STABLE"

    if accel < 0.5:
        return "COMPRESSION"

    if accel < 0.7:
        return "EXPANSION"

    return "CRISIS"
