import numpy as np
import pandas as pd

def sanitize(obj):

    # DataFrame → list of dict
    if isinstance(obj, pd.DataFrame):
        obj = obj.replace([np.inf, -np.inf], None)
        obj = obj.where(pd.notnull(obj), None)
        return obj.to_dict(orient="records")

    # numpy scalars
    if isinstance(obj, (np.floating, np.integer)):
        obj = obj.item()

    # floats
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj

    # dictionaries
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}

    # lists
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]

    # 🔥 FIX: handle custom classes like RegimeScoreResult
    if hasattr(obj, "__dict__"):
        return sanitize(obj.__dict__)

    return obj


def clean_scalar(x):
    if pd.isna(x) or np.isinf(x):
        return None
    return float(x)


def sanitize_keys(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            # convert key to string + remove illegal chars
            new_key = str(k).replace(".", "_").replace("$", "").replace("#", "").replace("[", "").replace("]", "").replace("/", "_")
            new_dict[new_key] = sanitize_keys(v)
        return new_dict
    elif isinstance(obj, list):
        return [sanitize_keys(i) for i in obj]
    else:
        return obj