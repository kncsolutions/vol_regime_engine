def theta_regime(option_chains):
    total_theta = sum(
        df["call_theta"].sum() + df["put_theta"].sum()
        for df in option_chains.values()
    )

    if total_theta < 0:
        return "POSITIVE_THETA_ENVIRONMENT"
    return "NEGATIVE_THETA_ENVIRONMENT"