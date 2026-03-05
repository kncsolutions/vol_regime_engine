def safe_get(row, key, default=None):
    try:
        return row[key]
    except Exception:
        return default


def safe_map(series, mapping, default=0):
    return series.map(mapping).fillna(default)