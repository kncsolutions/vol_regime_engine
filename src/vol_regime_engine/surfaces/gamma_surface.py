def gamma_surface_regime(option_chains):
    totals = {
        expiry: df["net_gex"].sum()
        for expiry, df in option_chains.items()
    }

    if all(v > 0 for v in totals.values()):
        return "LONG_GAMMA_SURFACE"
    elif all(v < 0 for v in totals.values()):
        return "SHORT_GAMMA_SURFACE"

    return "MIXED_SURFACE"
