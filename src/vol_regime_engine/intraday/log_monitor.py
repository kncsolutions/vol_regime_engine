from pathlib import Path
import json
import pandas as pd


class IntradayLogMonitor:

    def __init__(self, log_dir="engine_logs"):
        self.log_dir = Path(log_dir)

    # -----------------------------------
    # Load Logs
    # -----------------------------------

    def load_logs(self):

        files = sorted(
            self.log_dir.glob("run_*.json")
        )

        records = []

        for file in files:
            with open(file, "r") as f:
                data = json.load(f)
                record = data.get("output", {})
                record["timestamp"] = data.get("timestamp")
                records.append(record)

        return pd.DataFrame(records)

    # -----------------------------------
    # Intraday Change Detection
    # -----------------------------------

    def compute_intraday_changes(self, df):

        df = df.sort_values("timestamp")

        df["iv_change"] = df["iv"].diff()
        df["hv_change"] = df["hv"].diff()
        df["theta_change"] = df["total_theta"].diff()
        df["expected_pnl_change"] = df["expected_pnl"].diff()

        return df

    # -----------------------------------
    # Structural Alerts
    # -----------------------------------

    def detect_intraday_alerts(self, df, iv_threshold=0.01):

        alerts = []

        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else None

        if previous is None:
            return []

        # IV shock
        if abs(latest["iv_change"]) > iv_threshold:
            alerts.append("IV_SHOCK")

        # Gamma regime flip
        if latest["gamma_surface_regime"] != previous["gamma_surface_regime"]:
            alerts.append("GAMMA_REGIME_FLIP")

        # Strategy change
        if latest["strategy"]["name"] != previous["strategy"]["name"]:
            alerts.append("STRATEGY_SHIFT")

        # Expected PnL acceleration
        if latest["expected_pnl_change"] > 500:
            alerts.append("PNL_ACCELERATION")

        return alerts

    # ----------------------------
    # Rolling Stress Score
    # ----------------------------

    def compute_intraday_stress_score(self, df, window=5):

        df = df.sort_values("timestamp").copy()

        # Changes
        df["iv_change"] = df["iv"].diff()
        df["hv_change"] = df["hv"].diff()
        df["theta_change"] = df["total_theta"].diff()
        df["pnl_change"] = df["expected_pnl"].diff()

        # Normalize using rolling std
        for col in ["iv_change", "hv_change", "theta_change", "pnl_change"]:
            rolling_std = df[col].rolling(window).std()
            df[f"{col}_norm"] = df[col] / (rolling_std + 1e-8)

        df["intraday_stress_score"] = (
            df["iv_change_norm"].abs()
            + df["hv_change_norm"].abs()
            + df["theta_change_norm"].abs()
            + df["pnl_change_norm"].abs()
        )

        return df

    # ----------------------------
    # Regime Transition Matrix
    # ----------------------------

    def compute_regime_transitions(self, df, column):

        df = df.sort_values("timestamp")

        transitions = {}

        for i in range(1, len(df)):

            prev_state = df.iloc[i - 1][column]
            curr_state = df.iloc[i][column]

            if prev_state not in transitions:
                transitions[prev_state] = {}

            if curr_state not in transitions[prev_state]:
                transitions[prev_state][curr_state] = 0

            transitions[prev_state][curr_state] += 1

        return transitions

    def compute_transition_matrix(self, df, column):

        raw_counts = self.compute_regime_transitions(df, column)

        # Convert to probabilities
        matrix = {}

        for prev_state, next_states in raw_counts.items():

            total = sum(next_states.values())

            matrix[prev_state] = {
                state: count / total
                for state, count in next_states.items()
            }

        return matrix
