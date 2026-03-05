
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
