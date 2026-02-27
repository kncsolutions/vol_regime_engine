# systemic/convexity/engine.py

from .gex_surface import GEXSurface
from .vega_surface import VegaSurface
from .skew_model import SkewModel
from .gamma_walk import GammaMonteCarlo
from .inventory_model import ASInventoryModel
from .instability import InstabilityAnalyzer
from .crash_signal import crash_warning_signal

class ConvexityEngine:

    def __init__(self,
                 spot,
                 flip,
                 call_wall,
                 put_wall,
                 gex_profile,
                 vega_profile,
                 delta_slope,
                 delta_curvature):

        self.gex_surface = GEXSurface(flip, call_wall, put_wall, gex_profile)
        self.vega_surface = VegaSurface(vega_profile)
        self.skew_model = SkewModel(delta_slope, delta_curvature)
        self.spot = spot

    def run(self):

        mc = GammaMonteCarlo(self.gex_surface, 0.012, 0.02)
        paths = mc.simulate(self.spot)

        inventory_model = ASInventoryModel(
            self.gex_surface,
            self.vega_surface,
            gamma_risk=0.1,
            hedge_scale=0.000001
        )

        inventory = inventory_model.compute(paths)

        instability = InstabilityAnalyzer(
            self.gex_surface,
            self.vega_surface,
            self.skew_model,
            0.012,
            0.02
        )

        prob_instability, mean_time = instability.evaluate(paths, inventory)

        final_prices = paths[:, -1]

        result = {
            "prob_below_flip": (final_prices < self.gex_surface.flip).mean(),
            "mean_inventory": inventory[:, -1].mean(),
            "instability_probability": prob_instability,
            "mean_instability_time": mean_time
        }

        crash_flag = crash_warning_signal(
            result,
            self.skew_model.skew_pressure(),
            sum(self.vega_surface.values)
        )

        result["crash_flag"] = crash_flag

        return result