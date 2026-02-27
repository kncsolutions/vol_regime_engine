# systemic/convexity/gamma_walk.py

import numpy as np

class GammaMonteCarlo:

    def __init__(self, surface, base_vol, short_vol):

        self.surface = surface
        self.base_vol = base_vol
        self.short_vol = short_vol

    def simulate(self, spot, n_paths=1000, n_steps=120):

        dt = 1 / n_steps
        paths = np.zeros((n_paths, n_steps))
        paths[:, 0] = spot

        for i in range(n_paths):
            for t in range(1, n_steps):

                S = paths[i, t-1]
                gex = self.surface.get_local_gex(S)

                vol = self.base_vol if gex > 0 else self.short_vol
                drift = -0.15 * (S - self.surface.flip) / self.surface.flip if gex > 0 else -0.02

                dW = np.random.normal(0, np.sqrt(dt))
                dS = S * (drift * dt + vol * dW)
                paths[i, t] = S + dS

        return paths