# systemic/convexity/gex_surface.py

import numpy as np

class GEXSurface:

    def __init__(self, flip, call_wall, put_wall, gex_profile):
        """
        gex_profile: dict[strike -> net_gex_value]
        """

        self.flip = flip
        self.call_wall = call_wall
        self.put_wall = put_wall
        self.gex_profile = gex_profile

        self.strikes = np.array(list(gex_profile.keys()))
        self.values = np.array(list(gex_profile.values()))

    def get_local_gex(self, spot):

        # Gaussian-weighted interpolation around spot
        weights = np.exp(-0.001 * (self.strikes - spot) ** 2)
        weighted_gex = np.sum(weights * self.values) / np.sum(weights)

        return weighted_gex

    def gamma_state(self, spot):
        return np.sign(self.get_local_gex(spot))