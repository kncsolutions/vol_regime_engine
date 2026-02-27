from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import pandas as pd
import base64
import io
import matplotlib.pyplot as plt
from .dashboard_builder import DashboardBuilder
import html
import numpy as np
from dataclasses import asdict


class EngineLogger:

    def __init__(self, base_dir="engine_logs"):
        self.base_dir = Path(base_dir)
        self.dashboard = DashboardBuilder(base_dir)
        self.engine_version = "0.4.0"


    # --------------------------------------------------
    # Serialize option chains (unchanged)
    # --------------------------------------------------

    def _serialize_option_chains(self, option_chains: dict):

        serialized = {}

        for expiry, df in option_chains.items():
            serialized[expiry] = df.to_dict(orient="records")

        return serialized


    def format_value_for_html(self,v):
        """
        Formats dataclass, dict, list, numpy types safely for HTML display.
        """

        # Convert dataclass to dict
        if hasattr(v, "__dataclass_fields__"):
            v = asdict(v)

        # Convert numpy scalars to python types
        def convert_numpy(obj):
            if isinstance(obj, np.generic):
                return obj.item()
            return obj

        if isinstance(v, (dict, list)):
            clean_obj = json.loads(
                json.dumps(v, default=convert_numpy)
            )
            json_str = json.dumps(clean_obj, indent=4)
            return f"<pre>{html.escape(json_str)}</pre>"

        return html.escape(str(v))

    def to_ist(self,timestamp_str):
        dt = datetime.fromisoformat(timestamp_str)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        ist_time = dt.astimezone(ZoneInfo("Asia/Kolkata"))

        return ist_time.strftime("%Y-%m-%d %H:%M:%S IST")

    # --------------------------------------------------
    # HTML Generator (NEW — consistent with payload)
    # --------------------------------------------------

    def _generate_html(self, payload):

        regime_state = payload.get("regime_state", {})
        strategy_output = payload.get("strategy", [])
        chatgpt_response = payload.get("chatgpt_response", "")
        option_chains = payload.get("option_chains", {})
        timestamp = payload.get("timestamp_utc")
        ist_timestamp = self.to_ist(timestamp)

        html = f"""
        <html>
        <head>
            <title>Volatility Regime Snapshot</title>
            <style>
                body {{ font-family: Arial; margin: 40px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
                th, td {{ border: 1px solid #ccc; padding: 6px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                h1, h2 {{ margin-top: 30px; }}
                .meta {{ font-size: 12px; color: gray; }}
            </style>
        </head>
        <body>
        

        <h1>Volatility Regime Snapshot</h1>
        <div class="meta">        
            Timestamp: {ist_timestamp} <br>"
            Engine Version: {self.engine_version}
        </div>
        """

        # --------------------------------------------------
        # Regime State Table
        # --------------------------------------------------

        html += """
        <h2>Regime State</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
        """

        for k, v in regime_state.items():
            if k not in ["instability_pockets", "convexity_traps"]:

                # Format dict/list as pretty JSON
                formatted_value = self.format_value_for_html(v)
                html += f"<tr><td><b>{k}</b></td><td>{formatted_value}</td></tr>"

        html += "</table>"

        # --------------------------------------------------
        # Instability Pockets Table
        # --------------------------------------------------

        instability = regime_state.get("instability_pockets")

        if instability is not None:

            # Convert DataFrame to list-of-dict safely
            if hasattr(instability, "to_dict"):
                instability = instability.to_dict(orient="records")

            if isinstance(instability, list) and len(instability) > 0:

                html += """
                <h2>Instability Pockets</h2>
                <table>
                """

                headers = instability[0].keys()
                html += "<tr>" + "".join([f"<th>{h}</th>" for h in headers]) + "</tr>"

                for row in instability:
                    html += "<tr>" + "".join([f"<td>{row.get(h)}</td>" for h in headers]) + "</tr>"

                html += "</table>"

        # --------------------------------------------------
        # Convexity Traps Table
        # --------------------------------------------------

        convexity = regime_state.get("convexity_traps")

        if convexity is not None:

            if hasattr(convexity, "to_dict"):
                convexity = convexity.to_dict(orient="records")

            if isinstance(convexity, list) and len(convexity) > 0:

                html += """
                <h2>Convexity Traps</h2>
                <table>
                """

                headers = convexity[0].keys()
                html += "<tr>" + "".join([f"<th>{h}</th>" for h in headers]) + "</tr>"

                for row in convexity:
                    html += "<tr>" + "".join([f"<td>{row.get(h)}</td>" for h in headers]) + "</tr>"

                html += "</table>"
        # --------------------------------------------------
        # Surface & Skew Dynamics
        # --------------------------------------------------

        skew_change = regime_state.get("skew_change", {})
        surface_change = regime_state.get("surface_change", {})

        html += """
        <h2>Surface & Skew Dynamics</h2>
        <table>
        <tr><th>Metric</th><th>Value</th></tr>
        """

        # Parallel Shift
        parallel_shift = None
        if isinstance(surface_change, dict):
            parallel_shift = surface_change.get("parallel_shift")

        html += f"<tr><td>Parallel Surface Shift</td><td>{parallel_shift}</td></tr>"

        # Skew deltas
        skew_slope_delta = None
        skew_curvature_delta = None

        if isinstance(skew_change, dict):
            skew_slope_delta = skew_change.get("delta_slope")
            skew_curvature_delta = skew_change.get("delta_curvature")

        html += f"<tr><td>Skew Slope Δ</td><td>{skew_slope_delta}</td></tr>"
        html += f"<tr><td>Skew Curvature Δ</td><td>{skew_curvature_delta}</td></tr>"

        html += f"<tr><td>Skew Change Regime</td><td>{regime_state.get('skew_change_regime')}</td></tr>"
        html += f"<tr><td>Surface Shift Regime</td><td>{regime_state.get('surface_shift_regime')}</td></tr>"

        html += "</table>"


        # --------------------------------------------------
        # Inline GEX Mini Chart
        # --------------------------------------------------

        # --------------------------------------------------
        # Inline GEX Mini Chart (Enhanced)
        # --------------------------------------------------

        try:
            if option_chains:

                first_expiry = list(option_chains.values())[0]

                strikes = []
                gex = []

                for row in first_expiry:
                    if "strike" in row:
                        strikes.append(row["strike"])
                        gex.append(row.get("net_gex", 0))

                if len(strikes) > 0:

                    plt.figure(figsize=(7, 4))
                    plt.plot(strikes, gex)
                    plt.title("GEX Distribution")
                    plt.xlabel("Strike")
                    plt.ylabel("Net GEX")

                    # ------------------------------------------
                    # Gamma Flip Marker
                    # ------------------------------------------
                    gamma_flip = regime_state.get("gamma_flip")
                    if gamma_flip is not None:
                        plt.axvline(x=gamma_flip, linestyle="--")
                        plt.text(gamma_flip, max(gex), " Gamma Flip", rotation=90)

                    # ------------------------------------------
                    # Current Spot Vertical Line
                    # ------------------------------------------
                    current_spot = regime_state.get("current_spot")
                    if current_spot is not None:
                        plt.axvline(x=current_spot)
                        plt.text(current_spot, min(gex), " Spot", rotation=90)

                    # ------------------------------------------
                    # Instability Markers
                    # ------------------------------------------
                    instability = regime_state.get("instability_pockets")

                    if instability is not None:

                        if hasattr(instability, "to_dict"):
                            instability = instability.to_dict(orient="records")

                        if isinstance(instability, list):
                            inst_strikes = [
                                row.get("strike") for row in instability
                                if row.get("strike") is not None
                            ]

                            for s in inst_strikes:
                                if s in strikes:
                                    idx = strikes.index(s)
                                    plt.scatter(
                                        strikes[idx],
                                        gex[idx],
                                        marker="x"
                                    )

                    # ------------------------------------------
                    # Convexity Trap Markers
                    # ------------------------------------------
                    convexity = regime_state.get("convexity_traps")

                    if convexity is not None:

                        if hasattr(convexity, "to_dict"):
                            convexity = convexity.to_dict(orient="records")

                        if isinstance(convexity, list):
                            trap_strikes = [
                                row.get("strike") for row in convexity
                                if row.get("strike") is not None
                            ]

                            for s in trap_strikes:
                                if s in strikes:
                                    idx = strikes.index(s)
                                    plt.scatter(
                                        strikes[idx],
                                        gex[idx],
                                        marker="o"
                                    )

                    # ------------------------------------------
                    # Convert to Base64
                    # ------------------------------------------
                    import io, base64

                    buffer = io.BytesIO()
                    plt.savefig(buffer, format="png", bbox_inches="tight")
                    plt.close()
                    buffer.seek(0)

                    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

                    html += f"""
                    <h2>GEX Distribution</h2>
                    <img src="data:image/png;base64,{image_base64}" />
                    """

        except Exception:
            pass

        # --------------------------------------------------
        # Strategy Table
        # --------------------------------------------------

        html += """
        <h2>Strategy Output</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Bias</th>
                <th>Conviction</th>
                <th>Expected PnL</th>
            </tr>
        """

        if isinstance(strategy_output, list):
            for strat in strategy_output:
                html += f"""
                <tr>
                    <td>{strat.get("name")}</td>
                    <td>{strat.get("bias")}</td>
                    <td>{strat.get("conviction")}</td>
                    <td>{strat.get("expected_pnl")}</td>
                </tr>
                """

        html += "</table>"

        # --------------------------------------------------
        # LLM Interpretation
        # --------------------------------------------------

        html += f"""
        <h2>LLM Interpretation</h2>
        <p>{chatgpt_response}</p>
        </body>
        </html>
        """

        return html

    # --------------------------------------------------
    # Main Log Function (JSON + HTML)
    # --------------------------------------------------

    from datetime import datetime

    def log(
            self,
            option_chains: dict,
            spot_snapshot,
            regime_state: dict,
            strategy_output,
            chatgpt_response: str,
            session_type: str = "intraday"
    ):

        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H%M%S")

        underlying = regime_state.get("underlying", "UNKNOWN")

        target_dir = (
                self.base_dir
                / underlying
                / date_str
                / session_type
        )

        target_dir.mkdir(parents=True, exist_ok=True)

        json_path = target_dir / f"snapshot_{time_str}.json"
        html_path = target_dir / f"snapshot_{time_str}.html"

        payload = {
            "timestamp_utc": now.isoformat(),
            "engine_version": self.engine_version,
            "option_chains": self._serialize_option_chains(option_chains),
            "spot_snapshot": spot_snapshot.to_dict(orient="records"),
            "regime_state": regime_state,
            "strategy": strategy_output,
            "chatgpt_response": chatgpt_response
        }

        json_path.write_text(
            json.dumps(payload, indent=4, default=str),
            encoding="utf-8"
        )

        html_path.write_text(
            self._generate_html(payload),
            encoding="utf-8"
        )

        # Rebuild dashboards
        self.dashboard.build_daily_index(underlying, date_str)
        self.dashboard.build_underlying_index(underlying)
        self.dashboard.build_global_index()

        return {
            "json_path": json_path,
            "html_path": html_path
        }

