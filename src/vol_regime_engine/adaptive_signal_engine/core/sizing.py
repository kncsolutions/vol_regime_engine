from ..config import BASE_POSITION_SIZE


def compute_size(regime: str, matrix: dict):

    persistence = matrix[regime][regime]
    adverse_prob = 1 - persistence

    return BASE_POSITION_SIZE * (1 - adverse_prob)