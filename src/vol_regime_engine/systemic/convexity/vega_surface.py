# systemic/convexity/vega_surface.py

import numpy as np

class VegaSurface:

    def __init__(self, vega_profile):
        """
        vega_profile: dict[strike -> net_vega]
        """
        self.strikes = np.array(list(vega_profile.keys()))
        self.values = np.array(list(vega_profile.values()))

    def get_local_vega(self, spot):

        weights = np.exp(-0.001 * (self.strikes - spot) ** 2)
        weighted_vega = np.sum(weights * self.values) / np.sum(weights)

        return weighted_vega