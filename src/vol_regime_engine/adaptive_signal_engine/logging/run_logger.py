import json
from pathlib import Path
from datetime import datetime


class AdaptiveRunLogger:
    """
    Logs all adaptive signals from a single engine run
    into a uniquely timestamped JSON file.
    """

    def __init__(self, base_path="volatility_data"):
        self.base_path = Path(base_path)
        self.run_timestamp = datetime.now()
        self.signals = {}

    def add_signal(self, underlying: str, signal: dict):
        self.signals[underlying] = signal

    def save(self):

        date_folder = self.base_path / self.run_timestamp.strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        file_name = f"run_{self.run_timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
        file_path = date_folder / file_name

        output = {
            "run_timestamp": self.run_timestamp.isoformat(),
            "underlyings": self.signals
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4)

        return file_path