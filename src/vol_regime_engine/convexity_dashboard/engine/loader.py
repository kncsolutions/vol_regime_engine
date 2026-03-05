
import json
import pandas as pd
def load_json(path):

    import json
    import pandas as pd

    with open(path) as f:
        data = json.load(f)
    print(data)

    rows = []

    symbols = data.get("states", {})

    for symbol, v in symbols.items():

        adaptive = v.get("adaptive_signal", {})

        rows.append({
            "symbol": symbol,
            "bias": adaptive.get("bias"),
            "spot": v.get("current_spot"),
            "gamma_regime": adaptive.get("regime"),
            "iv_hv": v.get("iv_vs_hv"),
            "acceleration": v.get("acceleration_probability"),
            "theta": v.get("theta_regime"),
            "vega": v.get("vega_regime")
        })
    # print(rows)

    return pd.DataFrame(rows)
