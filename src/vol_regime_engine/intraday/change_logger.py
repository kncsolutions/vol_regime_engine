from pathlib import Path
from datetime import datetime
import json


class IntradayChangeLogger:

    def __init__(self, base_dir="engine_logs"):
        self.base_dir = Path(base_dir)

    # --------------------------------------------------
    # Compute change severity score
    # --------------------------------------------------

    def compute_severity_score(self, state_changes):

        severity = 0

        categorical = state_changes.get("categorical_changes", {})
        numeric = state_changes.get("numeric_changes", {})

        # Each categorical change = high impact
        severity += len(categorical) * 3

        # Each numeric change = medium impact
        severity += len(numeric) * 1

        return severity

    # --------------------------------------------------
    # Log intraday change
    # --------------------------------------------------

    def log(self, change_payload, session="intraday"):

        folder = self.base_dir / session / "state_changes"
        folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        severity = self.compute_severity_score(
            change_payload.get("state_changes", {})
        )

        log_data = {
            "timestamp_utc": timestamp,
            "change_severity_score": severity,
            **change_payload
        }

        file_path = folder / f"state_change_{timestamp}.json"

        with open(file_path, "w") as f:
            json.dump(log_data, f, indent=4, default=str)

        return file_path
