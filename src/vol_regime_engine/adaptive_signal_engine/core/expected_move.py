EXPECTED_MOVE = {
    "long_gamma": 0.4,
    "short_gamma": 1.2,
    "flip_zone": 1.8,
    "vega_expansion": 2.0,
}


def compute_expected_move(regime: str, matrix: dict):

    return sum(
        matrix[regime][r] * EXPECTED_MOVE[r]
        for r in matrix[regime]
    )