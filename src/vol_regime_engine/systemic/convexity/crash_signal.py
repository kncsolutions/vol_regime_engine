# systemic/convexity/crash_signal.py

def crash_warning_signal(result,
                         skew_pressure,
                         vega_magnitude):

    score = 0

    if result["instability_probability"] > 0.6:
        score += 1

    if skew_pressure > 0.3:
        score += 1

    if abs(result["mean_inventory"]) > 0.5:
        score += 1

    if abs(vega_magnitude) > 500000:
        score += 1

    if score >= 3:
        return "EARLY_CRASH_WARNING"

    if score == 2:
        return "ELEVATED_RISK"

    return "STABLE"