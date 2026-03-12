import firebase_admin
from firebase_admin import credentials, db

import pandas as pd
import numpy as np

import dash
from dash import dcc, html
from dash.dependencies import Input, Output

import plotly.graph_objects as go


class VolRegimeDashboard:

    def __init__(self, firebase_key: str, database_url: str):

        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_key)

            firebase_admin.initialize_app(
                cred,
                {"databaseURL": database_url}
            )

        self.root_ref = db.reference("vol-regime-metrics")

        self.app = dash.Dash(__name__)

        self.stock_list = self.get_stock_list()

        self.app.layout = self.build_layout()

        self.register_callbacks()

    # ----------------------------------
    # Load available stocks
    # ----------------------------------
    def get_stock_list(self):

        data = self.root_ref.get()

        if data is None:
            return []

        return list(data.keys())

    # ----------------------------------
    # Load stock data
    # ----------------------------------
    def load_stock_data(self, stock):

        ref = self.root_ref.child(stock).child("metrics")

        data = ref.get()

        if not data:
            return pd.DataFrame(), None

        df = pd.DataFrame(data).T
        df.index = (
            pd.to_datetime(df.index.astype(int), unit="s")
            .tz_localize("UTC")
            .tz_convert("Asia/Kolkata")
            .tz_localize(None)
        )
        df = df.sort_index()

        if "gamma_zones" in df.columns:
            df["gamma_flip"] = df["gamma_zones"].apply(
                lambda x: x.get("gamma_flip") if isinstance(x, dict) else None
            )

        option_chain = None

        if "option_chain" in df.columns:
            option_chain = df.iloc[-1]["option_chain"]

        return df, option_chain

    # ----------------------------------
    # Layout
    # ----------------------------------
    def build_layout(self):

        return html.Div([
            html.Div(

                id="market-banner",

                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "12px 20px",
                    "backgroundColor": "#111111",
                    "borderBottom": "1px solid #333333",
                    "fontSize": "16px",
                    "fontWeight": "bold"
                }

            ),

            html.H2("Volatility Regime Monitoring Dashboard"),

            dcc.Dropdown(
                id="stock-dropdown",
                options=[{"label": s, "value": s} for s in self.stock_list],
                value=self.stock_list[0] if self.stock_list else None,
                placeholder="Type to search stock...",
                searchable=True,
                clearable=False
            ),

            # -----------------------------
            # GRID SECTION (Time Series)
            # -----------------------------
            html.Div([

                dcc.Graph(id="spot-chart"),
                dcc.Graph(id="iv-chart"),
                dcc.Graph(id="hv-chart"),

                dcc.Graph(id="flip-chart"),
                dcc.Graph(id="k-chart"),
                dcc.Graph(id="bpr-chart"),

                dcc.Graph(id="i1-chart"),
                dcc.Graph(id="i2-chart"),
                dcc.Graph(id="amplification-chart"),

                dcc.Graph(id="fragility-chart"),

            ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr 1fr",
                    "gap": "10px"
                }),

            # -----------------------------
            # FULL WIDTH OPTION CHARTS
            # -----------------------------

            html.H3("Option Chain Structure"),

            dcc.Graph(id="oi-distribution"),
            dcc.Graph(id="dealer-heatmap"),
            dcc.Graph(id="gamma-exposure"),

            dcc.Graph(id="call-oi-change"),
            dcc.Graph(id="put-oi-change"),

            dcc.Graph(id="gamma-ladder"),
            dcc.Graph(id="hedging-pressure"),

            dcc.Graph(id="instability-surface"),

            html.Footer(

                html.Div([

                    html.Hr(),

                    html.Div(
                        "Volatility Regime Monitoring System",
                        style={
                            "textAlign": "center",
                            "fontSize": "16px",
                            "color": "#cccccc",
                            "fontWeight": "bold"
                        }
                    ),

                    html.Div(
                        "Metrics: k (Impact) • I1 (Linear Instability) • I2 (Convexity Instability) • Amplification • BPR",
                        style={
                            "textAlign": "center",
                            "fontSize": "12px",
                            "color": "#888888",
                            "marginTop": "6px"
                        }
                    ),

                    html.Div(
                        "Data Source: proprietary",
                        style={
                            "textAlign": "center",
                            "fontSize": "11px",
                            "color": "#777777",
                            "marginTop": "4px"
                        }
                    ),

                    html.Div(
                        "Developed by Pallav Nandi Chaudhuri",
                        style={
                            "textAlign": "center",
                            "fontSize": "12px",
                            "color": "#aaaaaa",
                            "marginTop": "10px",
                            "fontStyle": "italic"
                        }
                    ),

                ],
                    style={
                        "padding": "25px",
                        "marginTop": "50px"
                    })

            )

        ])

    # ----------------------------------
    # Time Series Chart
    # ----------------------------------
    def build_chart(self, df, column, title, color):

        fig = go.Figure()

        if column in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode="lines",
                    line=dict(color=color)
                )
            )

        fig.update_layout(
            template="plotly_dark",
            title=title,
            height=300
        )

        return fig

    # ----------------------------------
    # Strike vs Open Interest
    # ----------------------------------
    def build_oi_distribution(self, option_chain):

        fig = go.Figure()

        if option_chain:
            oc = pd.DataFrame(option_chain)

            fig.add_bar(x=oc["strike"], y=oc["call_oi"], name="Call OI")
            fig.add_bar(x=oc["strike"], y=oc["put_oi"], name="Put OI")

        fig.update_layout(
            template="plotly_dark",
            title="Strike vs Open Interest",
            height=500,
            barmode="group"
        )

        return fig

    # ----------------------------------
    # Dealer Heatmap
    # ----------------------------------
    def build_dealer_heatmap(self, option_chain):

        fig = go.Figure()

        if option_chain:
            oc = pd.DataFrame(option_chain)

            heat = [
                oc["call_oi_change"],
                oc["put_oi_change"]
            ]

            fig.add_trace(
                go.Heatmap(
                    z=heat,
                    x=oc["strike"],
                    y=["Call OI Change", "Put OI Change"],
                    colorscale="RdBu"
                )
            )

        fig.update_layout(
            template="plotly_dark",
            title="Dealer Position Heatmap",
            height=500
        )

        return fig

    # ----------------------------------
    # Gamma Exposure
    # ----------------------------------
    def build_gamma_exposure(self, option_chain):

        fig = go.Figure()

        if option_chain:
            oc = pd.DataFrame(option_chain)

            fig.add_bar(
                x=oc["strike"],
                y=oc["net_gex"],
                name="Gamma Exposure"
            )

        fig.update_layout(
            template="plotly_dark",
            title="Strike vs Gamma Exposure",
            height=500
        )

        return fig

    # ----------------------------------
    # Call OI Change
    # ----------------------------------
    def build_call_oi_change(self, option_chain):

        fig = go.Figure()

        if option_chain:
            oc = pd.DataFrame(option_chain)

            fig.add_bar(
                x=oc["strike"],
                y=oc["call_oi_change"]
            )

        fig.update_layout(
            template="plotly_dark",
            title="Call OI Change",
            height=500
        )

        return fig

    # ----------------------------------
    # Put OI Change
    # ----------------------------------
    def build_put_oi_change(self, option_chain):

        fig = go.Figure()

        if option_chain:
            oc = pd.DataFrame(option_chain)

            fig.add_bar(
                x=oc["strike"],
                y=oc["put_oi_change"]
            )

        fig.update_layout(
            template="plotly_dark",
            title="Put OI Change",
            height=500
        )

        return fig

    def build_gamma_ladder(self, option_chain):

        fig = go.Figure()

        if option_chain:
            oc = pd.DataFrame(option_chain)

            oc = oc.sort_values("strike")

            oc["cum_gex"] = oc["net_gex"].cumsum()

            fig.add_trace(
                go.Scatter(
                    x=oc["strike"],
                    y=oc["cum_gex"],
                    mode="lines",
                    name="Cumulative Gamma"
                )
            )

            fig.add_hline(y=0, line_dash="dash")

        fig.update_layout(
            template="plotly_dark",
            title="Gamma Ladder (Cumulative GEX)",
            height=500
        )

        return fig

    def build_hedging_pressure(self, option_chain):

        fig = go.Figure()

        if option_chain:
            oc = pd.DataFrame(option_chain)

            oc["hedge_pressure"] = abs(oc["net_gex"])

            fig.add_trace(
                go.Bar(
                    x=oc["strike"],
                    y=oc["hedge_pressure"],
                    name="Hedging Pressure"
                )
            )

        fig.update_layout(
            template="plotly_dark",
            title="Dealer Hedging Pressure",
            height=500
        )

        return fig

    def build_instability_surface(self, df):

        fig = go.Figure()

        required = [
            "spot",
            "gamma_flip",
            "linear_instability_I1",
            "convexity_instability_I2",
            "amplification_factor"
        ]

        if not all(col in df.columns for col in required):
            fig.update_layout(
                template="plotly_dark",
                title="Instability Surface (missing data)",
                height=600
            )
            return fig

        df = df.copy()

        # Distance from flip
        df["flip_distance"] = df["spot"] - df["gamma_flip"]

        # Ensure numeric types
        I1 = pd.to_numeric(df["linear_instability_I1"], errors="coerce")
        I2 = pd.to_numeric(df["convexity_instability_I2"], errors="coerce")
        amplification = pd.to_numeric(df["amplification_factor"], errors="coerce")

        # convert to positive marker sizes
        sizes = (amplification.abs() * 5).fillna(5)

        fig.add_trace(
            go.Scatter(
                x=df["flip_distance"],
                y=I1,
                mode="markers",
                marker=dict(
                    size=sizes.tolist(),
                    color=I2,
                    colorscale="Inferno",
                    showscale=True,
                    colorbar=dict(title="Convexity I2")
                ),
                name="Instability State"
            )
        )

        fig.update_layout(
            template="plotly_dark",
            title="Systemic Instability Surface",
            xaxis_title="Distance from Gamma Flip",
            yaxis_title="Linear Instability I1",
            height=600
        )

        return fig

    # ----------------------------------
    # Callbacks
    # ----------------------------------
    def register_callbacks(self):
        @self.app.callback(
            Output("stock-dropdown", "options"),
            Input("stock-dropdown", "search_value")
        )
        def update_dropdown_options(search_value):

            if not search_value:
                return [{"label": s, "value": s} for s in self.stock_list]

            filtered = [
                s for s in self.stock_list
                if search_value.lower() in s.lower()
            ]

            return [{"label": s, "value": s} for s in filtered]



        @self.app.callback(
            [
                Output("market-banner", "children"),


                Output("spot-chart", "figure"),
                Output("iv-chart", "figure"),
                Output("hv-chart", "figure"),

                Output("flip-chart", "figure"),
                Output("k-chart", "figure"),
                Output("bpr-chart", "figure"),

                Output("i1-chart", "figure"),
                Output("i2-chart", "figure"),
                Output("amplification-chart", "figure"),

                Output("fragility-chart", "figure"),

                Output("oi-distribution", "figure"),
                Output("dealer-heatmap", "figure"),
                Output("gamma-exposure", "figure"),

                Output("call-oi-change", "figure"),
                Output("put-oi-change", "figure"),

                Output("gamma-ladder", "figure"),
                Output("hedging-pressure", "figure"),

                Output("instability-surface", "figure"),

            ],
            Input("stock-dropdown", "value")

        )

        def update_dashboard(stock):

            df, option_chain = self.load_stock_data(stock)

            if df.empty:
                empty = go.Figure()
                return [empty] * 15

            spot = df.iloc[-1]["spot"] if "spot" in df.columns else None
            flip = df.iloc[-1]["gamma_flip"] if "gamma_flip" in df.columns else None

            distance = None
            regime = "UNKNOWN"

            if spot and flip:

                distance = spot - flip

                if spot > flip:
                    regime = "LONG GAMMA"
                    regime_color = "#00ff9c"
                else:
                    regime = "SHORT GAMMA"
                    regime_color = "#ff4d4d"
            else:
                regime_color = "#aaaaaa"

            last_update = df.index[-1].strftime("%Y-%m-%d %H:%M:%S IST")
            banner = [

                html.Div(
                    f"Market Regime: {regime}",
                    style={"color": "#FFFFFF"}
                ),

                html.Div(
                    f"Spot: {round(spot, 2)}",
                    style={"color": "#FFFFFF"}
                ),

                html.Div(
                    f"Gamma Flip: {round(flip, 2)}",
                    style={"color": "#FFFFFF"}
                ),

                html.Div(
                    f"Distance: {round(distance, 2)}",
                    style={"color": "#FFFFFF"}
                ),

                html.Div(
                    f"Last Update: {last_update}",
                    style={"color": "#FFFFFF"}
                )
            ]

            return (
                banner,

                self.build_chart(df, "spot", "Spot Price", "cyan"),
                self.build_chart(df, "iv", "Implied Volatility", "orange"),
                self.build_chart(df, "hv", "Historical Volatility", "green"),

                self.build_chart(df, "gamma_flip", "Gamma Flip", "yellow"),
                self.build_chart(df, "impact_coefficient_k", "Impact Coefficient k", "purple"),
                self.build_chart(df, "bifurcation_proximity_ratio", "BPR", "magenta"),

                self.build_chart(df, "linear_instability_I1", "I1", "red"),
                self.build_chart(df, "convexity_instability_I2", "I2", "blue"),
                self.build_chart(df, "amplification_factor", "Amplification", "gold"),

                self.build_chart(df, "fragility_score", "Fragility Score", "white"),

                self.build_oi_distribution(option_chain),
                self.build_dealer_heatmap(option_chain),
                self.build_gamma_exposure(option_chain),

                self.build_call_oi_change(option_chain),
                self.build_put_oi_change(option_chain),

                self.build_gamma_ladder(option_chain),
                self.build_hedging_pressure(option_chain),

                self.build_instability_surface(df),

            )

    # ----------------------------------
    # Run
    # ----------------------------------
    def run(self):

        self.app.run(debug=True)


if __name__ == "__main__":
    dashboard = VolRegimeDashboard(
        firebase_key="firebase_service_account.json",
        database_url="https://your-project-id-default-rtdb.firebaseio.com/"
    )

    dashboard.run()
