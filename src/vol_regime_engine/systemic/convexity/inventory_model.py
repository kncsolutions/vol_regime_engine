# systemic/convexity/inventory_model.py

class ASInventoryModel:

    def __init__(self, gex_surface, vega_surface,
                 gamma_risk, hedge_scale):

        self.gex_surface = gex_surface
        self.vega_surface = vega_surface
        self.gamma_risk = gamma_risk
        self.hedge_scale = hedge_scale

    def compute(self, paths):

        import numpy as np
        n_paths, n_steps = paths.shape
        inventory = np.zeros_like(paths)

        for i in range(n_paths):
            q = 0
            for t in range(1, n_steps):

                S_prev = paths[i, t-1]
                S_new = paths[i, t]
                dS = S_new - S_prev

                gex = self.gex_surface.get_local_gex(S_prev)
                vega = self.vega_surface.get_local_vega(S_prev)

                # Gamma hedge flow
                dq_gamma = -gex * dS * self.hedge_scale

                # Vega shock amplification
                dq_vega = -0.000001 * vega * abs(dS)

                # AS decay
                dq_as = -self.gamma_risk * q * (1 / n_steps)

                q += dq_gamma + dq_vega + dq_as
                inventory[i, t] = q

        return inventory