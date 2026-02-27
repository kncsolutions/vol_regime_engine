def vega_regime(option_chains):
    total_vega = sum(
        df["vega"].sum() for df in option_chains.values()
    )

    if total_vega > 0:
        return "LONG_VEGA"
    return "SHORT_VEGA"