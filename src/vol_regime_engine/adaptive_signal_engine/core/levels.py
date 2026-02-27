from ..config import BUFFER_PERCENT
from .instability import instability_intensity
BETA = 0.5  # stop widening factor
def generate_levels(state: dict, bias):

    gamma_flip = state.get("gamma_flip")
    call_wall = state.get("call_wall")
    put_wall = state.get("put_wall")
    recent_high = state.get("recent_high")
    recent_low = state.get("recent_low")
    instability = instability_intensity(state)
    stop_multiplier = 1 + BETA * instability

    # Helper to safely compare
    def safe_max(a, b):
        if a is None:
            return b
        if b is None:
            return a
        return max(a, b)

    def safe_min(a, b):
        if a is None:
            return b
        if b is None:
            return a
        return min(a, b)

    if bias.value == "trend_long":
        entry = safe_max(gamma_flip, recent_high)
        stop = gamma_flip

        return {
            "long_above": entry,
            "stop": stop,
        }

    if bias.value == "mean_revert":

        levels = {}

        if call_wall is not None:
            levels["short_from"] = call_wall
            levels["short_stop"] = call_wall * (1 + BUFFER_PERCENT * stop_multiplier)

        if put_wall is not None:
            levels["long_from"] = put_wall
            levels["long_stop"] = put_wall * (1 - BUFFER_PERCENT * stop_multiplier)

        return levels

    if bias.value == "breakout":

        if gamma_flip is None:
            return {}

        return {
            "long_above": gamma_flip,
            "long_stop": gamma_flip * (1 - BUFFER_PERCENT * stop_multiplier),
            "short_below": gamma_flip,
            "short_stop": gamma_flip * (1 + BUFFER_PERCENT * stop_multiplier)
        }

    return {}