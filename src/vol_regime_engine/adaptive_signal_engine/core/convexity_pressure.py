def convexity_direction(state: dict):
    """
    Returns directional skew signal in range [-1, 1].
    Positive = upside convexity pressure
    Negative = downside convexity pressure
    """

    call_gex = state.get("total_call_gex", 0)
    put_gex = state.get("total_put_gex", 0)

    total = abs(call_gex) + abs(put_gex)

    if total == 0:
        return 0.0

    return (call_gex - put_gex) / total