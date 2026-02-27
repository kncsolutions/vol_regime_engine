def short_vol_regime(state):
    return (
        state["gamma_surface_regime"] == "LONG_GAMMA_SURFACE"
        and state["vega_regime"] == "SHORT_VEGA"
        and state["iv_vs_hv"] == "IV_RICH"
    )


def long_vol_regime(state):
    return (
        state["gamma_surface_regime"] == "SHORT_GAMMA_SURFACE"
        and state["iv_vs_hv"] == "IV_CHEAP"
    )


def gamma_instability_breakout(state):
    return (
        state["instability_pockets"] is not None
        and state["gamma_surface_regime"] == "SHORT_GAMMA_SURFACE"
    )


def theta_harvest(state):
    return (
        state["theta_regime"] == "POSITIVE_THETA_ENVIRONMENT"
        and state["gamma_surface_regime"] == "LONG_GAMMA_SURFACE"
    )

def panic_skew_premium_sell(state):
    return (
        state.get("skew_regime") == "PANIC_SKEW"
        and state.get("gamma_surface_regime") == "LONG_GAMMA_SURFACE"
    )

def upside_momentum_play(state):
    return state.get("skew_regime") == "INVERTED_SKEW"

def normal_negative_skew(state):
    return state.get("skew_regime") == "NORMAL_NEGATIVE_SKEW"


def flat_skew(state):
    return state.get("skew_regime") == "FLAT_SKEW"
