from .strategies import StrategySignal

from .rules import (
    short_vol_regime,
    long_vol_regime,
    gamma_instability_breakout,
    theta_harvest,
    panic_skew_premium_sell,
    upside_momentum_play,
    normal_negative_skew,
    flat_skew
)


class StrategySelector:

    def select(self, state: dict):

        strategies = []

        # 1️⃣ Panic Skew Premium Sell
        if panic_skew_premium_sell(state):
            strategies.append(
                StrategySignal(
                    name="Downside Premium Sell",
                    bias="Short Put Spread",
                    rationale="Panic skew priced + long gamma surface",
                    risk_profile="Controlled",
                    conviction=0.85
                )
            )

        # 2️⃣ Gamma Breakout
        if gamma_instability_breakout(state):
            strategies.append(
                StrategySignal(
                    name="Gamma Breakout",
                    bias="Directional Momentum",
                    rationale="Short gamma + instability pocket",
                    risk_profile="High",
                    conviction=0.8
                )
            )

        # 3️⃣ Long Volatility
        if long_vol_regime(state):
            strategies.append(
                StrategySignal(
                    name="Long Volatility",
                    bias="Long Straddle",
                    rationale="Short gamma surface + IV cheap",
                    risk_profile="Medium",
                    conviction=0.7
                )
            )

        # 4️⃣ Short Volatility
        if short_vol_regime(state):
            strategies.append(
                StrategySignal(
                    name="Short Volatility",
                    bias="Iron Condor",
                    rationale="Long gamma surface + IV rich",
                    risk_profile="Controlled",
                    conviction=0.75
                )
            )

        # 5️⃣ Theta Harvest
        if theta_harvest(state):
            strategies.append(
                StrategySignal(
                    name="Theta Harvest",
                    bias="Credit Spread",
                    rationale="Positive theta + long gamma stabilization",
                    risk_profile="Low",
                    conviction=0.6
                )
            )

        # 6️⃣ Skew Reversal Play
        if state.get("skew_regime") == "INVERTED_SKEW":
            strategies.append(
                StrategySignal(
                    name="Upside Skew Reversal",
                    bias="Call Spread",
                    rationale="Upside IV bid extreme",
                    risk_profile="Medium",
                    conviction=0.65
                )
            )

        # 7️⃣ Vol Compression Trade
        if state.get("skew_regime") == "FLAT_SKEW" and \
           state.get("gamma_surface_regime") == "LONG_GAMMA_SURFACE":
            strategies.append(
                StrategySignal(
                    name="Vol Compression",
                    bias="Short Straddle (Hedged)",
                    rationale="Flat skew + stabilizing gamma",
                    risk_profile="Controlled",
                    conviction=0.7
                )
            )

        # 8️⃣ Upside Momentum Play (Inverted Skew)
        if upside_momentum_play(state):
            strategies.append(
                StrategySignal(
                    name="Upside Momentum Play",
                    bias="Long Calls / Call Spread",
                    rationale="Inverted skew → upside IV bid → squeeze risk",
                    risk_profile="Medium-High",
                    conviction=0.75
                )
            )

        # 9️⃣ Normal Negative Skew Strategy
        if normal_negative_skew(state):
            strategies.append(
                StrategySignal(
                    name="Neutral Premium Harvest",
                    bias="Put Credit Spread / Iron Condor",
                    rationale="Typical equity skew + no panic → stable premium environment",
                    risk_profile="Controlled",
                    conviction=0.65
                )
            )

        # 🔟 Flat Skew Strategy
        if flat_skew(state):
            strategies.append(
                StrategySignal(
                    name="Convexity Build",
                    bias="Long Straddle / Gamma Scalping",
                    rationale="Skew compression → potential regime expansion",
                    risk_profile="Medium",
                    conviction=0.7
                )
            )

        # If nothing triggered
        if not strategies:
            strategies.append(
                StrategySignal(
                    name="Neutral",
                    bias="Wait",
                    rationale="No dominant regime alignment",
                    risk_profile="None",
                    conviction=0.3
                )
            )

        # Sort by conviction descending
        strategies = sorted(
            strategies,
            key=lambda x: x.conviction,
            reverse=True
        )

        return strategies
