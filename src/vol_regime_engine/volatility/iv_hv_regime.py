def detect_iv_hv_regime(current_iv, current_hv, threshold=0.01):
    spread = current_iv - current_hv

    if spread > threshold:
        return "IV_RICH"
    elif spread < -threshold:
        return "IV_CHEAP"
    return "NEUTRAL"