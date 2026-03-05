import os
from pathlib import Path

project_name = "convexity_dashboard"

folders = [
    "data",
    "engine",
    "dashboard",
    "runner"
]

files = {}

# -------------------------
# LOADER
# -------------------------

files["engine/loader.py"] = """
import json
import pandas as pd

def load_json(path):

    with open(path) as f:
        data = json.load(f)

    rows = []

    for symbol, v in data.items():

        adaptive = v.get("adaptive_signal", {})

        rows.append({
            "symbol": symbol,
            "bias": adaptive.get("bias"),
            "gamma_regime": v.get("gamma_regime"),
            "iv_hv": v.get("iv_vs_hv"),
            "acceleration": v.get("acceleration_probability"),
            "theta": v.get("theta_environment"),
            "vega": v.get("vega_regime")
        })

    return pd.DataFrame(rows)
"""

# -------------------------
# SCORING
# -------------------------

files["engine/scoring.py"] = """
def convexity_score(df):

    gamma_weight = {
        "SHORT_GAMMA": 10,
        "FLIP_ZONE": 8,
        "LONG_GAMMA": 4
    }

    iv_weight = {
        "IV_CHEAP": 8,
        "IV_RICH": 5
    }

    df["gamma_score"] = df.gamma_regime.map(gamma_weight).fillna(5)
    df["iv_score"] = df.iv_hv.map(iv_weight).fillna(5)

    df["convexity_score"] = (
        0.5 * df.acceleration.fillna(0) * 10
        + 0.3 * df.gamma_score
        + 0.2 * df.iv_score
    )

    return df.sort_values("convexity_score", ascending=False)
"""

# -------------------------
# FILTER
# -------------------------

files["engine/opportunity_filter.py"] = """
def filter_opportunities(df):

    return df[
        (df.acceleration > 0.4)
    ]
"""

# -------------------------
# TRADE CLASSIFIER
# -------------------------

files["engine/trade_classifier.py"] = """
def classify_trade(row):

    if row.gamma_regime == "SHORT_GAMMA":

        if row.bias == "trend_long":
            return "Call Buy"

        if row.bias == "trend_short":
            return "Put Buy"

    if row.gamma_regime == "FLIP_ZONE":
        return "Straddle"

    if row.gamma_regime == "LONG_GAMMA":
        return "Iron Condor"

    return "Watch"
"""

# -------------------------
# MARKET STATE
# -------------------------

files["engine/market_state.py"] = """
def classify_market_state(accel):

    if accel < 0.3:
        return "STABLE"

    if accel < 0.5:
        return "COMPRESSION"

    if accel < 0.7:
        return "EXPANSION"

    return "CRISIS"
"""

# -------------------------
# DASHBOARD
# -------------------------

files["dashboard/dashboard.py"] = """
import plotly.express as px
from dash import Dash, html, dcc, dash_table

def create_dashboard(df):

    fig1 = px.scatter(
        df,
        x="acceleration",
        y="symbol",
        size="convexity_score",
        color="gamma_regime",
        title="Convexity Opportunity Map"
    )

    fig2 = px.bar(
        df.head(20),
        x="symbol",
        y="convexity_score",
        color="gamma_regime",
        title="Top Opportunities"
    )

    fig3 = px.treemap(
        df,
        path=["gamma_regime", "bias", "symbol"],
        values="convexity_score",
        title="Gamma Structure"
    )

    app = Dash(__name__)

    app.layout = html.Div([

        html.H1("Convexity Opportunity Dashboard"),

        dcc.Graph(figure=fig1),

        dcc.Graph(figure=fig2),

        dcc.Graph(figure=fig3),

        dash_table.DataTable(
            data=df.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df.columns],
            filter_action="native",
            sort_action="native",
            page_size=20
        )

    ])

    return app
"""

# -------------------------
# RUNNER
# -------------------------

files["runner/run_dashboard.py"] = """
from engine.loader import load_json
from engine.scoring import convexity_score
from engine.opportunity_filter import filter_opportunities
from engine.trade_classifier import classify_trade
from dashboard.dashboard import create_dashboard

df = load_json("data/opportunities.json")

df = convexity_score(df)

df = filter_opportunities(df)

df["trade"] = df.apply(classify_trade, axis=1)

app = create_dashboard(df)

app.run(debug=True)
"""

# -------------------------
# REQUIREMENTS
# -------------------------

files["requirements.txt"] = """
dash
plotly
pandas
"""

files["README.md"] = """
Convexity Opportunity Dashboard

Run:

pip install -r requirements.txt
python runner/run_dashboard.py
"""

# -------------------------
# CREATE PROJECT
# -------------------------

root = Path(project_name)
root.mkdir(exist_ok=True)

for folder in folders:
    (root / folder).mkdir(exist_ok=True)

for path, content in files.items():

    full_path = root / path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, "w") as f:
        f.write(content)

print("Project created:", project_name)