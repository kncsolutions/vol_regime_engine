from pathlib import Path
import json
import pandas as pd
import numpy as np


class SnapshotIntradayMonitor:

    def __init__(self, base_log_dir="engine_logs"):
        self.base_dir = Path(base_log_dir)

    # =========================================================
    # Load Snapshots + Convert Option Chains to DataFrames
    # =========================================================

    def load_snapshots(self, session="intraday"):

        if session == "all":
            dirs = [
                self.base_dir / "intraday",
                self.base_dir / "overnight",
            ]
        else:
            dirs = [self.base_dir / session]

        records = []

        for directory in dirs:
            if not directory.exists():
                continue

            files = sorted(directory.glob("snapshot_*.json"))

            for file in files:
                with open(file, "r") as f:
                    data = json.load(f)

                record = {
                    "timestamp": data.get("timestamp_utc"),
                }

                # -------------------------------------------------
                # Spot
                # -------------------------------------------------
                spot_data = data.get("spot_snapshot", [])
                if spot_data:
                    record["spot"] = spot_data[0].get("close")

                # -------------------------------------------------
                # Convert Option Chains (list → DataFrame)
                # -------------------------------------------------
                option_chains = data.get("option_chains", {})

                total_theta = 0.0
                total_gex = 0.0
                iv_values = []

                for expiry, strike_list in option_chains.items():

                    if not strike_list:
                        continue

                    df = pd.DataFrame(strike_list)

                    # Numeric safety
                    numeric_cols = [
                        "call_theta", "put_theta",
                        "net_gex", "iv"
                    ]

                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")

                    # Aggregate
                    if "call_theta" in df.columns:
                        total_theta += df["call_theta"].sum()

                    if "put_theta" in df.columns:
                        total_theta += df["put_theta"].sum()

                    if "net_gex" in df.columns:
                        total_gex += df["net_gex"].sum()

                    if "iv" in df.columns:
                        iv_values.append(df["iv"].mean())

                record["total_theta"] = total_theta
                record["total_gex"] = total_gex
                record["iv"] = np.mean(iv_values) if iv_values else None

                # -------------------------------------------------
                # Regime State
                # -------------------------------------------------
                regime = data.get("regime_state", {})
                for key, value in regime.items():
                    if isinstance(value, (dict, list)):
                        record[key] = json.dumps(value)
                    else:
                        record[key] = value

                # -------------------------------------------------
                # Strategy (robust handling)
                # -------------------------------------------------
                strategy = data.get("strategy", {})

                if isinstance(strategy, list):
                    primary = strategy[0] if strategy else {}
                elif isinstance(strategy, dict):
                    primary = strategy
                else:
                    primary = {}

                record["strategy_name"] = primary.get("name")
                record["expected_pnl"] = primary.get("expected_pnl")

                records.append(record)

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        return df

    # =========================================================
    # Intraday Metric Computation
    # =========================================================

    def compute_intraday_metrics(self, df):

        if df.empty:
            return df

        df = df.copy()

        # Spot returns
        if "spot" in df.columns:
            df["log_return"] = np.log(df["spot"] / df["spot"].shift(1))

        # Changes
        for col in ["iv", "total_theta", "total_gex", "expected_pnl"]:
            if col in df.columns:
                df[f"{col}_change"] = df[col].diff()

        # Strategy shift
        if "strategy_name" in df.columns:
            df["strategy_shift"] = (
                df["strategy_name"] != df["strategy_name"].shift(1)
            )

        return df

    # =========================================================
    # Rolling Intraday Stress Score
    # =========================================================

    def compute_stress_score(self, df, window=5):

        if df.empty:
            return df

        df = df.copy()

        change_cols = [
            "iv_change",
            "total_theta_change",
            "total_gex_change",
            "expected_pnl_change",
        ]

        components = []

        for col in change_cols:

            if col in df.columns:
                rolling_std = df[col].rolling(window).std()
                norm = df[col] / (rolling_std + 1e-8)
                components.append(norm.abs())
            else:
                components.append(pd.Series(0, index=df.index))

        df["intraday_stress_score"] = sum(components)

        return df

    # =========================================================
    # Transition Matrix
    # =========================================================

    def compute_transition_matrix(self, df, column):

        if df.empty or column not in df.columns:
            return {}

        transitions = {}

        for i in range(1, len(df)):
            prev_state = df.iloc[i - 1][column]
            curr_state = df.iloc[i][column]

            if prev_state not in transitions:
                transitions[prev_state] = {}

            if curr_state not in transitions[prev_state]:
                transitions[prev_state][curr_state] = 0

            transitions[prev_state][curr_state] += 1

        matrix = {}

        for prev, next_states in transitions.items():
            total = sum(next_states.values())
            matrix[prev] = {
                state: count / total
                for state, count in next_states.items()
            }

        return matrix

    # =========================================================
    # Regime Half-Life
    # =========================================================

    def compute_half_life(self, df, column):

        matrix = self.compute_transition_matrix(df, column)

        half_lives = {}

        for state, transitions in matrix.items():

            p = transitions.get(state, 0)

            if p <= 0 or p >= 1:
                half_life = float("inf")
            else:
                half_life = np.log(0.5) / np.log(p)

            half_lives[state] = half_life

        return half_lives
