import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import plotly.io as pio
from pathlib import Path


def save_dashboard_html(figures, run_json_path):

    run_dir = Path(run_json_path).parent
    run_name = Path(run_json_path).stem

    output_file = run_dir / f"{run_name}_dashboard.html"

    html_parts = []

    for fig in figures:
        html_parts.append(
            pio.to_html(
                fig,
                include_plotlyjs="cdn",
                full_html=False
            )
        )

    html = f"""
    <html>
    <head>
        <title>Convexity Opportunity Dashboard</title>
        <style>
        body {{
            background-color:#111111;
            color:#e6e6e6;
            font-family: Arial;
            padding:20px;
        }}
        h1 {{
            text-align:center;
        }}
        footer {{
            margin-top:40px;
            border-top:1px solid #333;
            padding-top:10px;
            text-align:center;
            font-size:12px;
        }}
        </style>
    </head>

    <body>

    <h1>Convexity Opportunity Dashboard</h1>

    {''.join(html_parts)}

    <footer>
    Convexity Volatility Engine • Dealer Hedging Simulator • Convexity Ladder
    </footer>

    </body>
    </html>
    """

    with open(output_file, "w") as f:
        f.write(html)

    print(f"Dashboard HTML saved → {output_file}")

# ==============================
# Utility Safety Helpers
# ==============================

def ensure_columns(df, cols):

    for c in cols:
        if c not in df.columns:
            df[c] = None

    return df


def safe_df(df):

    if df is None or df.empty:

        return pd.DataFrame({
            "symbol": ["No Opportunities"],
            "gamma_regime": ["neutral"],
            "bias": ["neutral"],
            "convexity_score": [0],
            "acceleration": [0],
            "dealer_pressure": [0],
        })

    return df


# ==============================
# Dashboard
# ==============================

def create_dashboard(df, simulations=None):

    df = safe_df(df)

    df = ensure_columns(df, [
        "symbol",
        "gamma_regime",
        "bias",
        "convexity_score",
        "acceleration",
        "dealer_pressure",
        "target1",
        "target2",
        "spot",
        "gamma_flip",
        "shock_score"
    ])

    # ==========================
    # Convexity Opportunity Map
    # ==========================

    fig1 = px.scatter(
        df,
        x="acceleration",
        y="symbol",
        size="convexity_score",
        color="gamma_regime",
        hover_data=[
            "bias",
            "dealer_pressure",
            "target1",
            "target2"
        ],
        title="Convexity Opportunity Map",
        template="plotly_dark",
        height=500
    )

    # ==========================
    # Top Opportunities
    # ==========================

    fig2 = px.bar(
        df.head(20),
        x="symbol",
        y="convexity_score",
        color="gamma_regime",
        title="Top Convexity Opportunities",
        template="plotly_dark",
        height=400
    )

    # ==========================
    # Gamma Treemap (Safe)
    # ==========================

    safe_tree = df.dropna(subset=["gamma_regime", "bias", "symbol"])

    if not safe_tree.empty:

        fig3 = px.treemap(
            safe_tree,
            path=["gamma_regime", "bias", "symbol"],
            values="convexity_score",
            title="Gamma Regime Structure",
            template="plotly_dark",
            height=450
        )

    else:

        fig3 = go.Figure()

    # ==========================
    # Shock Detector
    # ==========================

    if "shock_score" in df.columns and df["shock_score"].notna().any():

        fig4 = px.bar(
            df.sort_values("shock_score", ascending=False).head(15),
            x="symbol",
            y="shock_score",
            color="gamma_regime",
            title="Convexity Shock Detector",
            template="plotly_dark",
            height=400
        )

    else:

        fig4 = go.Figure()

    # ==========================
    # Convexity Ladder Targets
    # ==========================

    if df["target1"].notna().any():

        fig5 = px.scatter(
            df,
            x="symbol",
            y="target1",
            size="convexity_score",
            color="gamma_regime",
            hover_data=["target2", "dealer_pressure"],
            title="Convexity Ladder Targets",
            template="plotly_dark",
            height=400
        )

    else:

        fig5 = go.Figure()

    # ==========================
    # Convexity Surface
    # ==========================

    fig6 = px.scatter(
        df,
        x="acceleration",
        y="dealer_pressure",
        size="convexity_score",
        color="gamma_regime",
        text="symbol",
        title="Convexity Surface Map",
        template="plotly_dark",
        height=500
    )

    fig6.add_hline(y=4, line_dash="dot")
    fig6.add_vline(x=0.4, line_dash="dot")

    # ==========================
    # Gamma Flip Map
    # ==========================

    if df["gamma_flip"].notna().any():

        fig7 = px.scatter(
            df,
            x="spot",
            y="gamma_flip",
            size="convexity_score",
            color="gamma_regime",
            text="symbol",
            title="Gamma Flip Map",
            template="plotly_dark",
            height=450
        )

    else:

        fig7 = go.Figure()

    # ==========================
    # Dash App
    # ==========================

    app = Dash(__name__)

    app.layout = html.Div([

        html.H1(
            "Convexity Opportunity Dashboard",
            style={"textAlign": "center"}
        ),

        dcc.Graph(id="convexity-map", figure=fig1),

        html.Div([
            dcc.Graph(figure=fig2),
            dcc.Graph(figure=fig3)
        ], style={"display": "flex"}),

        html.Div([
            dcc.Graph(figure=fig4),
            dcc.Graph(figure=fig5)
        ], style={"display": "flex"}),

        dcc.Graph(figure=fig6),

        dcc.Graph(figure=fig7),

        html.H2("Symbol Analytics Panel"),

        html.Div([
            dcc.Graph(id="hedging-path"),
            dcc.Graph(id="ladder-chart")
        ], style={"display": "flex"}),

        html.Div([
            dcc.Graph(id="dealer-gauge"),
            dcc.Graph(id="shock-gauge")
        ], style={"display": "flex"}),

        dash_table.DataTable(

            data=df.to_dict("records"),

            columns=[{"name": i, "id": i} for i in df.columns],

            filter_action="native",
            sort_action="native",
            page_size=20,

            style_table={
                "overflowX": "auto",
                "marginTop": "20px"
            },

            style_header={
                "backgroundColor": "#222",
                "color": "white",
                "fontWeight": "bold"
            },

            style_cell={
                "backgroundColor": "#111",
                "color": "#e6e6e6",
                "border": "1px solid #333",
                "padding": "6px",
                "textAlign": "left"
            },

            style_data_conditional=[

                {
                    "if": {"filter_query": "{gamma_regime} = short_gamma"},
                    "backgroundColor": "#2b0000",
                    "color": "white"
                },

                {
                    "if": {"filter_query": "{gamma_regime} = flip_zone"},
                    "backgroundColor": "#3d3200",
                    "color": "white"
                },

                {
                    "if": {"filter_query": "{gamma_regime} = long_gamma"},
                    "backgroundColor": "#001f33",
                    "color": "white"
                }

            ]
        ),

        html.Footer(
            "Convexity Volatility Engine • Dealer Hedging Simulator • Convexity Ladder",
            style={
                "textAlign": "center",
                "padding": "15px",
                "borderTop": "1px solid #333",
                "marginTop": "40px"
            }
        )

    ], style={
        "backgroundColor": "#111111",
        "color": "#e6e6e6",
        "padding": "20px"
    })

    # ==========================
    # Callbacks
    # ==========================

    @app.callback(
        Output("hedging-path", "figure"),
        Input("convexity-map", "clickData")
    )
    def update_hedging(clickData):

        if clickData is None or simulations is None:
            return go.Figure()

        symbol = clickData["points"][0]["y"]

        if symbol not in simulations:
            return go.Figure()

        prices = simulations[symbol]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=prices,
                mode="lines+markers"
            )
        )

        fig.update_layout(
            template="plotly_dark",
            title=f"Hedging Simulation: {symbol}"
        )

        return fig

    @app.callback(
        Output("dealer-gauge", "figure"),
        Input("convexity-map", "clickData")
    )
    def dealer_gauge(clickData):

        if clickData is None:
            return go.Figure()

        symbol = clickData["points"][0]["y"]

        pressure = df[df.symbol == symbol]["dealer_pressure"].iloc[0]

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pressure,
            title={"text": "Dealer Pressure"},
            gauge={"axis": {"range": [0, 10]}}
        ))

        return fig

    @app.callback(
        Output("shock-gauge", "figure"),
        Input("convexity-map", "clickData")
    )
    def shock_gauge(clickData):

        if clickData is None:
            return go.Figure()

        symbol = clickData["points"][0]["y"]

        score = df[df.symbol == symbol]["shock_score"].iloc[0]

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Shock Probability"},
            gauge={"axis": {"range": [0, 1]}}
        ))

        return fig

    figures = [fig1, fig2, fig3, fig4, fig5, fig6, fig7]

    return app, figures