from pathlib import Path
from datetime import datetime
import json
import io
import base64
import matplotlib.pyplot as plt
from ..middleware.dashboard_builder import DashboardBuilder




class IntradayChangeHTMLLogger:

    def __init__(self, base_dir="engine_logs"):
        self.base_dir = Path(base_dir)

    # --------------------------------------------------
    # Severity Score
    # --------------------------------------------------

    def compute_severity(self, state_changes):

        categorical = state_changes.get("categorical_changes", {})
        numeric = state_changes.get("numeric_changes", {})

        return len(categorical) * 3 + len(numeric)

    # --------------------------------------------------
    # HTML Generator
    # --------------------------------------------------

    def _generate_html(self, payload):

        timestamp = payload.get("timestamp_utc")
        latest_snapshot = payload.get("latest_snapshot", [])
        state_changes = payload.get("state_changes", {})
        transition_matrix = payload.get("gamma_transition_matrix", {})
        half_life = payload.get("gamma_half_life", {})

        severity = self.compute_severity(state_changes)

        html = f"""
        <html>
        <head>
            <title>Intraday State Change Report</title>
            <style>
                body {{ font-family: Arial; margin: 40px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
                th, td {{ border: 1px solid #ccc; padding: 6px; }}
                th {{ background-color: #f2f2f2; }}
                h1, h2 {{ margin-top: 30px; }}
                .meta {{ font-size: 12px; color: gray; }}
                .severity {{ font-weight: bold; }}
            </style>
        </head>
        <body>

        <h1>Intraday State Change Report</h1>
        <div class="meta">
            Timestamp: {timestamp}
        </div>

        <h2>Change Severity Score</h2>
        <div class="severity">{severity}</div>
        """

        # --------------------------------------------------
        # Latest Snapshot
        # --------------------------------------------------

        if latest_snapshot:
            snapshot = latest_snapshot[0]

            html += """
            <h2>Latest Snapshot</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
            """

            for k, v in snapshot.items():
                html += f"<tr><td>{k}</td><td>{v}</td></tr>"

            html += "</table>"

        # --------------------------------------------------
        # Categorical Changes
        # --------------------------------------------------

        categorical = state_changes.get("categorical_changes", {})

        html += """
        <h2>Categorical Changes</h2>
        <table>
            <tr><th>Field</th><th>Previous</th><th>Current</th></tr>
        """

        for field, change in categorical.items():
            html += f"""
            <tr>
                <td>{field}</td>
                <td>{change.get('previous')}</td>
                <td>{change.get('current')}</td>
            </tr>
            """

        html += "</table>"


        # --------------------------------------------------
        # Numeric Changes
        # --------------------------------------------------

        numeric = state_changes.get("numeric_changes", {})

        html += """
        <h2>Numeric Changes</h2>
        <table>
            <tr><th>Field</th><th>Previous</th><th>Current</th><th>Delta</th></tr>
        """

        for field, change in numeric.items():
            html += f"""
            <tr>
                <td>{field}</td>
                <td>{change.get('previous')}</td>
                <td>{change.get('current')}</td>
                <td>{change.get('delta')}</td>
            </tr>
            """

        html += "</table>"

        # --------------------------------------------------
        # Gamma Transition Matrix
        # --------------------------------------------------

        if transition_matrix:

            html += "<h2>Gamma Transition Matrix</h2><table>"

            states = list(transition_matrix.keys())
            headers = list(next(iter(transition_matrix.values())).keys())

            html += "<tr><th>From \\ To</th>"
            for h in headers:
                html += f"<th>{h}</th>"
            html += "</tr>"

            for from_state, transitions in transition_matrix.items():
                html += f"<tr><td>{from_state}</td>"
                for to_state in headers:
                    html += f"<td>{round(transitions.get(to_state, 0), 3)}</td>"
                html += "</tr>"

            html += "</table>"

        # --------------------------------------------------
        # Half-Life
        # --------------------------------------------------

        if half_life:

            html += """
            <h2>Gamma Regime Half-Life</h2>
            <table>
                <tr><th>Regime</th><th>Half-Life</th></tr>
            """

            for regime, hl in half_life.items():
                html += f"<tr><td>{regime}</td><td>{hl}</td></tr>"

            html += "</table>"

        html += "</body></html>"

        return html

    # --------------------------------------------------
    # Log Method
    # --------------------------------------------------

    def log(self, payload, session="intraday"):

        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H%M%S")

        latest_snapshot = payload.get("latest_snapshot", [])
        snapshot = latest_snapshot[0] if latest_snapshot else {}

        underlying = snapshot.get("underlying", "UNKNOWN")

        target_dir = (
                self.base_dir
                / underlying
                / date_str
                / session
                / "state_changes"
        )

        target_dir.mkdir(parents=True, exist_ok=True)

        payload["timestamp_utc"] = now.isoformat()

        json_path = target_dir / f"change_{time_str}.json"
        html_path = target_dir / f"change_{time_str}.html"

        json_path.write_text(
            json.dumps(payload, indent=4, default=str),
            encoding="utf-8"
        )

        html_path.write_text(
            self._generate_html(payload),
            encoding="utf-8"
        )
        dashboard = DashboardBuilder(self.base_dir)
        dashboard.build_daily_index(underlying, date_str)
        dashboard.build_underlying_index(underlying)
        dashboard.build_global_index()

        return {
            "json_path": json_path,
            "html_path": html_path
        }

