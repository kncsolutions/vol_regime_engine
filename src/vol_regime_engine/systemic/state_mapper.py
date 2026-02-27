# systemic/state_mapper.py

def map_convexity_state(result):

    state = {}

    state["gamma_transition_risk"] = result["prob_below_flip"]
    state["inventory_stress"] = result["mean_inventory"]
    state["convexity_instability"] = result["instability_probability"]
    state["time_to_break"] = result["mean_instability_time"]

    if result["instability_probability"] > 0.6:
        state["regime_flag"] = "SHORT_GAMMA_TRANSITION"
    else:
        state["regime_flag"] = "STABLE_LONG_GAMMA"

    return state