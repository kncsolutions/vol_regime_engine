from pathlib import Path
from datetime import datetime
import json
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
from .run_excel_builder import RunExcelBuilder
from .run_pdf_builder import RunPDFBuilder
from ..systemic.diagnostics import SystemicDiagnostics
class RunAggregator:

    def __init__(self, base_dir="engine_logs"):

        self.base_dir = Path(base_dir)
        self.runs_dir = self.base_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        self.current_run_id = None
        self.current_run_path = None
        self.run_payload = None

    # --------------------------------------------------
    # Start New Run
    # --------------------------------------------------

    def start_new_run(self):

        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H%M%S")

        date_dir = self.runs_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        run_id = f"{date_str}_{time_str}"

        self.current_run_id = run_id
        self.current_run_path = date_dir / f"run_{run_id}.json"

        self.run_payload = {
            "run_id": run_id,
            "timestamp_utc": now.isoformat(),
            "states": {}
        }

    # --------------------------------------------------
    # Append Underlying State
    # --------------------------------------------------

    def append_state(self, underlying: str, state: dict):

        if self.run_payload is None:
            raise RuntimeError("Call start_new_run() first.")

        self.run_payload["states"][underlying] = state

    # --------------------------------------------------
    # Generate HTML Dashboard
    # --------------------------------------------------

    def _generate_html(self):

        states = self.run_payload["states"]

        html = f"""
        <html>
        <head>
            <title>Run Dashboard</title>
            <style>
                body {{ font-family: Arial; margin: 40px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ccc; padding: 6px; }}
                th {{ background-color: #f2f2f2; }}
                h1, h2 {{ margin-top: 30px; }}
                details {{ margin-bottom: 20px; }}
            </style>
        </head>
        <body>

        <h1>Multi-Asset Run Dashboard</h1>
        <p>Run ID: {self.current_run_id}</p>
        """

        # --------------------------------------------------
        # Summary Table
        # --------------------------------------------------

        html += """
        <h2>Regime Summary</h2>
        <table>
            <tr>
                <th>Underlying</th>
                <th>Gamma</th>
                <th>IV</th>
                <th>HV</th>
                <th>Skew</th>
                <th>Surface</th>
                <th>Expected PnL</th>
            </tr>
        """

        gamma_regimes = {}
        iv_values = []

        for underlying, state in states.items():
            gamma = state.get("gamma_surface_regime")
            iv = state.get("iv")
            hv = state.get("hv")
            skew = state.get("skew_regime")
            surface = state.get("surface_shift_regime")
            pnl = state.get("expected_pnl")

            gamma_regimes[gamma] = gamma_regimes.get(gamma, 0) + 1
            iv_values.append(iv)

            html += f"""
            <tr>
                <td>{underlying}</td>
                <td>{gamma}</td>
                <td>{iv}</td>
                <td>{hv}</td>
                <td>{skew}</td>
                <td>{surface}</td>
                <td>{pnl}</td>
            </tr>
            """

        html += "</table>"

        # --------------------------------------------------
        # Detailed State Tables
        # --------------------------------------------------

        html += "<h2>Detailed States</h2>"



        # --------------------------------------------------
        # Detailed State Tables
        # --------------------------------------------------

        html += "<h2>Detailed States</h2>"

        for underlying, state in states.items():

            html += f"""
            <details>
            <summary><strong>{underlying}</strong></summary>
            """

            # -------------------------------
            # Main Scalar Fields
            # -------------------------------

            html += """
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
            """

            for key, value in state.items():

                if key in ["instability_pockets", "convexity_traps", "adaptive_signal"]:
                    continue

                if isinstance(value, (dict, list)):
                    value = str(value)

                html += f"<tr><td>{key}</td><td>{value}</td></tr>"

            html += "</table>"

            # -------------------------------
            # Instability Pockets Table
            # -------------------------------

            instability = state.get("instability_pockets")

            if instability is not None:

                # Case 1 — It is a real DataFrame
                if isinstance(instability, pd.DataFrame):

                    if not instability.empty:
                        html += "<h4>Instability Pockets</h4>"
                        html += instability.to_html(index=False)

                # Case 2 — It is a stringified DataFrame
                elif isinstance(instability, str):

                    if "Empty DataFrame" not in instability:

                        try:
                            df = pd.read_fwf(io.StringIO(instability))

                            if not df.empty:
                                html += "<h4>Instability Pockets</h4>"
                                html += df.to_html(index=False)

                        except Exception:
                            html += f"<pre>{instability}</pre>"

            # -------------------------------
            # Convexity Traps Table
            # -------------------------------

            convexity = state.get("convexity_traps")

            if convexity is not None:

                if isinstance(convexity, pd.DataFrame):

                    if not convexity.empty:
                        html += "<h4>Convexity Traps</h4>"
                        html += convexity.to_html(index=False)

                elif isinstance(convexity, str):

                    if "Empty DataFrame" not in convexity:

                        try:
                            df = pd.read_fwf(io.StringIO(convexity))

                            if not df.empty:
                                html += "<h4>Convexity Traps</h4>"
                                html += df.to_html(index=False)

                        except Exception:
                            html += f"<pre>{convexity}</pre>"

            # -------------------------------
            # Adaptive Signal Table
            # -------------------------------

            adaptive = state.get("adaptive_signal")

            if isinstance(adaptive, dict):

                html += "<h4>Adaptive Signal</h4>"
                html += "<table><tr><th>Field</th><th>Value</th></tr>"

                for k, v in adaptive.items():

                    if isinstance(v, dict):
                        html += f"<tr><td>{k}</td><td>{json.dumps(v, indent=2)}</td></tr>"
                    else:
                        html += f"<tr><td>{k}</td><td>{v}</td></tr>"

                html += "</table>"

            html += "</details>"

        html += "</body></html>"

        return html

    # --------------------------------------------------
    # Finalize
    # --------------------------------------------------

    def finalize(self):

        if self.run_payload is None:
            raise RuntimeError("Call start_new_run() first.")

        # Write JSON
        self.current_run_path.write_text(
            json.dumps(self.run_payload, indent=4, default=str),
            encoding="utf-8"
        )

        # Write HTML
        html_path = self.current_run_path.with_suffix(".html")
        html_path.write_text(self._generate_html(), encoding="utf-8")

        # Write Excel
        excel_path = self.current_run_path.with_suffix(".xlsx")

        diagnostics = SystemicDiagnostics()
        states = self.run_payload["states"]

        self.run_payload["systemic_metrics"] = {
            "gamma_alignment": diagnostics.gamma_alignment(states),
            "vol_expansion_breadth": diagnostics.vol_expansion_breadth(states),
            "correlation_shock": diagnostics.correlation_shock(states),
            "regime_sync": diagnostics.regime_sync(states),
            "systemic_risk_index": diagnostics.systemic_risk_index(states),
            "cross_asset_flip_risk": diagnostics.cross_asset_flip_risk(states),
            "early_crash_warning": diagnostics.early_crash_warning(states),
        }

        excel_builder = RunExcelBuilder()
        excel_builder.build(self.run_payload, excel_path)

        pdf_path = self.current_run_path.with_suffix(".pdf")

        pdf_builder = RunPDFBuilder()
        pdf_builder.build(self.run_payload, str(pdf_path))

        return {
            "json_path": self.current_run_path,
            "html_path": html_path,
            "excel_path": excel_path
        }