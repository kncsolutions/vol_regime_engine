def compute_oi_walls(option_chains):
    """
    Computes aggregated call and put OI walls across expiries.
    """

    call_oi_by_strike = {}
    put_oi_by_strike = {}

    for expiry, df in option_chains.items():

        for _, row in df.iterrows():

            strike = row["strike"]

            call_oi = row.get("call_oi", 0)
            put_oi = row.get("put_oi", 0)

            call_oi_by_strike[strike] = (
                call_oi_by_strike.get(strike, 0) + call_oi
            )

            put_oi_by_strike[strike] = (
                put_oi_by_strike.get(strike, 0) + put_oi
            )

    call_wall = max(call_oi_by_strike, key=call_oi_by_strike.get, default=None)
    put_wall = max(put_oi_by_strike, key=put_oi_by_strike.get, default=None)

    return call_wall, put_wall