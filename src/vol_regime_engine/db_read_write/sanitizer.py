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

    return obj


def clean_scalar(x):
    if pd.isna(x) or np.isinf(x):
        return None
    return float(x)