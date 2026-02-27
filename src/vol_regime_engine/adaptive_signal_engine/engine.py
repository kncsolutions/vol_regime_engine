from .transition.matrix import DEFAULT_MATRIX
from .core.bias import compute_bias
from .core.levels import generate_levels
from .core.sizing import compute_size
from .core.expected_move import compute_expected_move
from .core.regime_mapper import normalize_regime


def run_adaptive_signal_engine(state: dict):

    raw_regime = state["gamma_surface_regime"]
    regime = normalize_regime(raw_regime)

    matrix = DEFAULT_MATRIX

    bias, score = compute_bias(regime, matrix, state)

    levels = generate_levels(state, bias)

    size = compute_size(regime, matrix)

    expected_move = compute_expected_move(regime, matrix)

    return {
        "regime": regime,
        "bias": bias.value,
        "bias_score": score,
        "levels": levels,
        "position_size": size,
        "expected_move": expected_move,
        "transition_probs": matrix[regime],
    }