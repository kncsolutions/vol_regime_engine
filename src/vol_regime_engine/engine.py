from openai import OpenAI

from .gamma.gex import calculate_gex
from .gamma.gamma_flip import identify_gamma_flip
from .gamma.instability import detect_instability
from .gamma.convexity import detect_convexity_traps
from .surfaces.gamma_surface import gamma_surface_regime
from .vega.vega_regime import vega_regime
from .theta.theta_regime import theta_regime

from .volatility.hv import calculate_hv, get_current_hv
from .volatility.iv_utils import get_atm_iv
from .volatility.iv_hv_regime import detect_iv_hv_regime
from .volatility.skew_surface import VolatilityStructureStore
from .volatility.skew_regime import SkewRegimeClassifier
from .volatility.surface_dynamics import VolatilityDynamics

from .middleware.logging import EngineLogger
from .strategy.selector import StrategySelector
from .pnl.expected_pnl import ExpectedPnLModel
from .intraday.snapshot_monitor import SnapshotIntradayMonitor
from .intraday.state_change import StateChangeAnalyzer
from .intraday.change_logger import IntradayChangeLogger
from .intraday.change_html_logger import IntradayChangeHTMLLogger
from .middleware.run_aggregator import RunAggregator
from .openinterest.oiwalls import compute_oi_walls
from .systemic.convexity.engine import ConvexityEngine
from .systemic.convexity_shock_engine  import (
    ConvexityShockEngine,
    ConvexityShockInputs,
    StrikeGEX
)
from .systemic.flow_impact_monitor import (
    FlowImpactMonitor,
    FlowImpactInputs
)
from .futurestates.futures_state_engine import FuturesStateEngine
from .scoring.regime_scorer import RegimeScorer
from .indicators.atr import ATRCalculator
from .core.engine_state import EngineState
from .scaling.simple_gex_scale import SimpleGEXScale
from vol_regime_engine.adaptive_signal_engine.engine import run_adaptive_signal_engine
from vol_regime_engine.adaptive_signal_engine.engine import run_adaptive_signal_engine
from vol_regime_engine.adaptive_signal_engine.logging.run_logger import AdaptiveRunLogger
from screening.regime_classifier import RegimeClassifier
from screening.structure_extractor import StructureExtractor
from screening.action_engine import ActionEngine
from screening.regime_confidence import RegimeConfidenceModel
from screening.acceleration_model import AccelerationProbabilityModel


class VolRegimeEngine:

    def __init__(self, lot_size: int = 65, enable_logging=True):

        self.lot_size = lot_size

        # Core components
        self.strategy_selector = StrategySelector()
        self.pnl_model = ExpectedPnLModel()

        # Vol structure
        self.vol_store = VolatilityStructureStore()
        self.skew_classifier = SkewRegimeClassifier()
        self.vol_dynamics = VolatilityDynamics()

        # Logging
        self.enable_logging = enable_logging
        self.logger = EngineLogger() if enable_logging else None
        self.change_logger = IntradayChangeLogger()
        self.change_html_logger = IntradayChangeHTMLLogger()

        self.aggregator = RunAggregator()
        self.aggregator.start_new_run()

    # =========================================================
    # MAIN RUN
    # =========================================================

    def run(
            self,
            option_chains: dict,
            spot_history,
            future_ohlc: dict,
            lot_size: int = 65,
            session_type="overnight",
            underlying="NIFTY",
            chatgpt=False
    ):
        self.lot_size = lot_size

        # ---------------------------------------
        # 1️⃣ Compute GEX per expiry
        # ---------------------------------------

        for expiry, df in option_chains.items():
            option_chains[expiry] = calculate_gex(
                df,
                lot_size=self.lot_size
            )

        # ---------------------------------------
        # 2️⃣ Surface Regimes
        # ---------------------------------------

        gamma_surface = gamma_surface_regime(option_chains)
        vega_state = vega_regime(option_chains)
        theta_state = theta_regime(option_chains)

        # ---------------------------------------
        # 3️⃣ Spot & IV/HV
        # ---------------------------------------

        current_spot = spot_history["close"].iloc[-1]
        current_hv = get_current_hv(spot_history, window=20)

        nearest_df = list(option_chains.values())[0]
        nearest_expiry = nearest_df.iloc[0]["expiry_date"]

        current_iv = get_atm_iv(
            nearest_df,
            spot=current_spot,
            iv_col="iv"
        )

        iv_hv_state = detect_iv_hv_regime(current_iv, current_hv)

        # ---------------------------------------
        # 4️⃣ Skew + Surface Storage
        # ---------------------------------------

        skew_data = self.vol_store.extract_skew(
            nearest_df,
            spot=current_spot
        )
        self.vol_store.save_skew(
            nearest_expiry,
            underlying,
            session_type,
            skew_data
        )

        surface_data = self.vol_store.extract_surface(
            option_chains,
            spot=current_spot
        )
        self.vol_store.save_surface(underlying, session_type, surface_data)

        skew_metrics = self.skew_classifier.compute_skew_metrics(
            nearest_df,
            current_spot
        )
        skew_regime = self.skew_classifier.classify(skew_metrics)

        skew_change = self.vol_dynamics.compute_skew_change_from_store(
            underlying=underlying,
            session_type=session_type,
            spot=current_spot
        )
        surface_change = self.vol_dynamics.compute_surface_change_from_store(
            underlying=underlying,
            session_type=session_type
        )

        skew_change_regime = self.vol_dynamics.classify_skew_change(skew_change)
        surface_shift_regime = self.vol_dynamics.classify_surface_shift(surface_change)

        # ---------------------------------------
        # 5️⃣ Gamma Structure
        # ---------------------------------------

        gamma_flip = identify_gamma_flip(nearest_df)
        instability = detect_instability(nearest_df)
        convexity = detect_convexity_traps(nearest_df)

        call_wall, put_wall = compute_oi_walls(option_chains)

        # ---------------------------------------
        # 5.1️⃣ Build GEX + Vega Profiles
        # ---------------------------------------

        gex_profile = (
            nearest_df.groupby("strike")["net_gex"]
            .sum()
            .to_dict()
        )

        vega_profile = (
            nearest_df.groupby("strike")["vega"]
            .sum()
            .to_dict()
        )

        # ---------------------------------------
        # 6️⃣ Build Clean State (NO large objects)
        # ---------------------------------------

        state = {
            "gamma_surface_regime": gamma_surface,
            "vega_regime": vega_state,
            "theta_regime": theta_state,
            "iv_vs_hv": iv_hv_state,
            "iv": current_iv,
            "hv": current_hv,
            "gamma_flip": gamma_flip,
            "call_wall": call_wall,
            "put_wall": put_wall,
            "recent_high": spot_history["high"].iloc[-1],
            "recent_low": spot_history["low"].iloc[-1],
            "instability_pockets": instability,
            "convexity_traps": convexity,
            "skew_regime": skew_regime,
            "skew_change": skew_change,
            "surface_change": surface_change,
            "skew_change_regime": skew_change_regime,
            "surface_shift_regime": surface_shift_regime,
            "current_spot": current_spot,
            "underlying": underlying
        }
        adaptive_output = run_adaptive_signal_engine(state)

        state["adaptive_signal"] = adaptive_output

        # ---------------------------------------
        # 6.5️⃣ Systemic Convexity Block
        # ---------------------------------------

        try:
            convexity_result = ConvexityEngine(
                spot=current_spot,
                flip=gamma_flip,
                call_wall=call_wall,
                put_wall=put_wall,
                gex_profile=gex_profile,
                vega_profile=vega_profile,
                delta_slope=skew_change.get("delta_slope", 0),
                delta_curvature=skew_change.get("delta_curvature", 0)
            ).run()

        except Exception as e:
            convexity_result = {
                "prob_below_flip": 0,
                "mean_inventory": 0,
                "instability_probability": 0,
                "mean_instability_time": None,
                "crash_flag": "ERROR"
            }

        state["convexity"] = {
            "gamma_transition_risk": convexity_result["prob_below_flip"],
            "inventory_stress": convexity_result["mean_inventory"],
            "convexity_instability": convexity_result["instability_probability"],
            "time_to_break": convexity_result["mean_instability_time"],
            "crash_flag": convexity_result["crash_flag"]
        }

        # ---------------------------------------
        # 6.6️⃣ Flow Impact + Nonlinear Convexity Layer (SAFE ADD)
        # ---------------------------------------

        try:

            # --- Build strike objects for systemic layer ---
            strike_objects = [
                StrikeGEX(strike=k, net_gex=v)
                for k, v in gex_profile.items()
            ]

            # --- Estimate local GEX near spot ---
            local_net_gex = sum(gex_profile.values())

            # --- Estimate gradient safely ---
            sorted_strikes = sorted(gex_profile.keys())
            lower_strikes = [s for s in sorted_strikes if s <= current_spot]
            upper_strikes = [s for s in sorted_strikes if s > current_spot]

            if lower_strikes and upper_strikes:
                lower = max(lower_strikes)
                upper = min(upper_strikes)

                dS = upper - lower
                if dS != 0:
                    gex_gradient = (
                                           gex_profile.get(upper, 0) -
                                           gex_profile.get(lower, 0)
                                   ) / dS
                else:
                    gex_gradient = 0
            else:
                gex_gradient = 0

            # --- Realized vol proxy ---
            daily_realized_vol = current_hv / 100 if current_hv else 0.01

            # --- Futures volume proxy (safe fallback) ---
            daily_futures_volume = max(
                future_ohlc[list(future_ohlc.keys())[0]][
                    list(future_ohlc[list(future_ohlc.keys())[0]].keys())[0]
                ]["volume"].sum(),
                1
            )

            baseline_impact_k = 1e-7  # configurable baseline

            # ------------------------------------------------
            # Flow Impact Monitor
            # ------------------------------------------------

            flow_monitor = FlowImpactMonitor()

            flow_result = flow_monitor.evaluate(
                FlowImpactInputs(
                    net_gex=local_net_gex,
                    gex_gradient=gex_gradient,
                    exogenous_flow=0,  # no live imbalance in batch run
                    daily_realized_vol=daily_realized_vol,
                    daily_futures_volume=daily_futures_volume,
                    fragility_score=state["convexity"]["convexity_instability"] * 100,
                    baseline_impact_k=baseline_impact_k
                )
            )

            # ------------------------------------------------
            # Nonlinear Convexity Shock Engine
            # ------------------------------------------------
            atr_calc = ATRCalculator(lookback=5, method="ema")

            result = atr_calc.latest_atr_values(spot_history)

            shock_engine = ConvexityShockEngine()

            shock_result = shock_engine.compute(
                ConvexityShockInputs(
                    spot=current_spot,
                    strikes=strike_objects,
                    lot_size=self.lot_size,
                    atr_points=state.get("atr_pct", 1) * current_spot / 100,
                    flip_level=gamma_flip,
                    fragility_score=state["convexity"]["convexity_instability"] * 100,
                    daily_realized_vol=daily_realized_vol,
                    daily_futures_volume=daily_futures_volume,
                    baseline_impact_k=baseline_impact_k,
                    shock_percent=0.02,
                    notional_shock_rupees=10_000 * 1e7,  # ₹10,000 Cr,
                    target_percent_move = result["atr_pct"] / 100  # 1% move
                )
            )

            state["systemic"] = {
                "flow_impact": flow_result,
                "convexity_shock": shock_result
            }

        except Exception as e:

            state["systemic"] = {
                "flow_impact": {},
                "convexity_shock": {},
                "error": str(e)
            }

        # ---------------------------------------
        # 7️⃣ Strategy Selection
        # ---------------------------------------

        strategies = self.strategy_selector.select(state)

        strategy_outputs = []

        for strat in strategies:
            expected_pnl = self.pnl_model.evaluate(
                strat.name,
                state
            )

            strategy_outputs.append({
                "name": strat.name,
                "bias": strat.bias,
                "conviction": strat.conviction,
                "expected_pnl": expected_pnl
            })

        # ---------------------------------------
        # 7.1 Screening
        # ---------------------------------------
        regime_classifier = RegimeClassifier()
        structure_extractor = StructureExtractor()
        action_engine = ActionEngine()

        regime = regime_classifier.classify(state)
        structure = structure_extractor.extract(state)
        action_plan = action_engine.generate(regime, structure, state)

        state["screening_output"] = action_plan

        confidence_model = RegimeConfidenceModel()
        accel_model = AccelerationProbabilityModel()

        state["regime_confidence"] = confidence_model.compute(state)
        state["acceleration_probability"] = accel_model.compute(state)
        # ---------------------------------------
        # 7.2️⃣ Systemic Override Logic
        # ---------------------------------------

        if state["convexity"]["crash_flag"] == "EARLY_CRASH_WARNING":
            state["systemic_regime"] = "CRASH_PRECURSOR"

        elif state["convexity"]["convexity_instability"] > 0.6:
            state["systemic_regime"] = "SHORT_GAMMA_TRANSITION"

        else:
            state["systemic_regime"] = "STABLE"

        # ---------------------------------------
        # 8️⃣ Future state analysis (optional)
        # ---------------------------------------
        future_keys = []
        futures_engine = FuturesStateEngine()
        for expiry, tf_dict in future_ohlc.items():
            for tf, df in tf_dict.items():
                key = f"{"Future"}_{expiry}_{tf}"
                future_keys.append(key)
                state[key] = self.compute_future_regime(df, gamma_surface)

        # ---------------------------------------
        # 8️⃣ Regime Scoring
        # ---------------------------------------



        state["atr_pct"] = result["atr_pct"]
        scale_estimator = SimpleGEXScale(alpha=2.0, min_scale=1e8)
        gex_scale = scale_estimator.compute_scale(option_chains)
        try:
            vol_expanding = state["skew_change"]["delta_atm_iv"] > 0
        except Exception as e:
            vol_expanding = False
        engine_state = EngineState(
            option_chains=option_chains,
            spot=current_spot,
            gamma_flip_level=gamma_flip,
            atr_pct=state["atr_pct"],
            gex_scale=gex_scale,
            iv=current_iv,
            hv=current_hv,
            vol_expanding=vol_expanding,
            futures_state=state[future_keys[0]]["categorical_changes"]["future_base_state"],
            skew_state=state["skew_regime"],
            surface_state=state["surface_shift_regime"],
            cross_asset_raw_score=0
        )
        scorer = RegimeScorer()

        try:
            result = scorer.compute(engine_state.__dict__)

        except Exception as e:
            # Hard fallback safety
            print("Regime scoring failed:", e)
            result = {"regime_score": 0, "strategy_bias": "NEUTRAL_OPTIONALITY_SMALL_SIZE"}

        state["regime_score"]= result




        # ---------------------------------------
        # 8️⃣ LLM Interpretation (optional)
        # ---------------------------------------
        if chatgpt:
            # OpenAI client (uses env variable)
            client = OpenAI(
                api_key="")

            response = client.responses.create(
                model="gpt-5",
                input=f"Interpret this volatility regime state: {state}"
            )
            interpretation = response.output_text
        else:
            interpretation = 'Manual Interpretation Required'

        print(interpretation)

        # ---------------------------------------
        # 9️⃣ Logging
        # ---------------------------------------

        if self.enable_logging:
            self.logger.log(
                option_chains=option_chains,
                spot_snapshot=spot_history.tail(1),
                regime_state=state,
                strategy_output=strategy_outputs,
                chatgpt_response=interpretation,
                session_type=session_type
            )
            self.aggregator.append_state(
                underlying,
                state
            )

        return {
            "state": state,
            "strategies": strategy_outputs,
            "llm_interpretation": interpretation
        }

    def log_finalize(self):
        run_path = self.aggregator.finalize()
        print("Run saved at:", run_path)

    # =========================================================
    # Intraday Monitor
    # =========================================================

    def check_intraday_changes(self):

        monitor = SnapshotIntradayMonitor()
        analyzer = StateChangeAnalyzer()

        df = monitor.load_snapshots(session="intraday")

        if df.empty or len(df) < 2:
            return {}

        df = monitor.compute_intraday_metrics(df)
        df = monitor.compute_stress_score(df)

        gamma_matrix = monitor.compute_transition_matrix(
            df,
            "gamma_surface_regime"
        )

        gamma_half_life = monitor.compute_half_life(
            df,
            "gamma_surface_regime"
        )

        state_changes = analyzer.analyze(df)

        result = {
            "latest_snapshot": df.tail(1).to_dict(orient="records"),
            "gamma_transition_matrix": gamma_matrix,
            "gamma_half_life": gamma_half_life,
            "state_changes": state_changes
        }

        # 🔥 NEW: log change snapshot
        self.change_html_logger.log(result, session="intraday")

        return result

    def run_adaptive_signals(self, states_by_underlying: dict):
        """
        states_by_underlying:
            {
                "NIFTY": state_dict,
                "BANKNIFTY": state_dict,
                ...
            }
        """

        logger = AdaptiveRunLogger()

        results = {}

        for underlying, state in states_by_underlying.items():
            signal = run_adaptive_signal_engine(state)

            logger.add_signal(underlying, signal)
            results[underlying] = signal

        file_path = logger.save()

        print(f"Adaptive run log saved: {file_path}")

        return results

    def _run_convexity_block(self, snapshot):

        convexity_engine = ConvexityEngine(
            spot=snapshot["current_spot"],
            flip=snapshot["gamma_flip"],
            call_wall=snapshot["call_wall"],
            put_wall=snapshot["put_wall"],
            gex_profile=snapshot["gex_profile"],
            vega_profile=snapshot["vega_profile"],
            delta_slope=snapshot["skew_change"]["delta_slope"],
            delta_curvature=snapshot["skew_change"]["delta_curvature"]
        )

        return convexity_engine.run()

    # --------------------------------------------------
    # Main Regime Computation
    # --------------------------------------------------

    def compute_future_regime(self, futures_df, gamma_surface_regime):
        categorical_changes = {}
        numeric_changes = {}

        # --------------------------------------------------
        # Futures Structural State
        # --------------------------------------------------
        futures_engine = FuturesStateEngine()

        futures_output = futures_engine.evaluate_latest(futures_df, gamma_surface_regime)
        categorical_changes["future_base_state"] = futures_output["future_base_state"]
        categorical_changes["futures_state"] = futures_output["composite_state"]
        categorical_changes["gamma_regime"] = futures_output["gamma_regime"]

        numeric_changes["futures_severity"] = futures_output["severity_score"]
        numeric_changes["convexity_risk"] = futures_output["convexity_risk"]

        # --------------------------------------------------
        # Return consolidated state object
        # --------------------------------------------------

        return {
            "categorical_changes": categorical_changes,
            "numeric_changes": numeric_changes,
            "meta": {
                "transition_matrix": futures_output["transition_matrix"]
            }
        }
