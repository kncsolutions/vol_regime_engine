from ..enums import Bias
from .instability import instability_intensity
from .convexity_pressure import convexity_direction

ALPHA = 0.30  # directional instability weight
from ..config import (
    BIAS_UPPER_THRESHOLD,
    BIAS_LOWER_THRESHOLD,
)

DIRECTIONAL_MAP = {
    "long_gamma": 0.0,
    "short_gamma": 1.0,
    "flip_zone": 0.5,
    "vega_expansion": 1.0,
}


def compute_bias(regime: str, matrix: dict, state: dict):

    probs = matrix.get(regime, matrix["flip_zone"])

    base_score = sum(
        probs[next_regime] * DIRECTIONAL_MAP[next_regime]
        for next_regime in probs
    )

    instability = instability_intensity(state)
    skew_dir = convexity_direction(state)

    # directional convexity adjustment
    adjustment = ALPHA * instability * skew_dir

    adjusted_score = base_score + adjustment

    adjusted_score = max(0, min(1, adjusted_score))

    if adjusted_score > BIAS_UPPER_THRESHOLD:
        return Bias.TREND_LONG, adjusted_score
    elif adjusted_score < BIAS_LOWER_THRESHOLD:
        return Bias.MEAN_REVERT, adjusted_score
    else:
        return Bias.BREAKOUT, adjusted_score