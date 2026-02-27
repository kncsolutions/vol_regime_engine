import json
from pathlib import Path
from datetime import datetime


def save_signal(underlying: str, signal: dict):

    date = datetime.now().strftime("%Y-%m-%d")
    folder = Path("volatility_data") / underlying / date
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / "adaptive_signal.json"

    with open(file_path, "w") as f:
        json.dump(signal, f, indent=4)

    return file_path