# systemic/convexity/instability.py

class InstabilityAnalyzer:

    def __init__(self, gex_surface, vega_surface,
                 skew_model, base_vol, short_vol):

        self.gex_surface = gex_surface
        self.vega_surface = vega_surface
        self.skew_model = skew_model
        self.base_vol = base_vol
        self.short_vol = short_vol

    def evaluate(self, paths, inventory):

        import numpy as np

        n_paths, n_steps = paths.shape
        instability_times = []

        skew_pressure = self.skew_model.skew_pressure()

        for i in range(n_paths):
            for t in range(1, n_steps):

                S = paths[i, t]
                q = inventory[i, t]

                gex = self.gex_surface.get_local_gex(S)
                vega = self.vega_surface.get_local_vega(S)

                base = self.base_vol if gex > 0 else self.short_vol

                # Volatility feedback from inventory + vega + skew
                vol = base * (
                    1
                    + 2 * abs(q)
                    + 0.000001 * abs(vega)
                    + 0.1 * skew_pressure
                )

                if vol > 3 * self.base_vol:
                    instability_times.append(t)
                    break

        if len(instability_times) == 0:
            return 0, None

        return len(instability_times) / n_paths, np.mean(instability_times)