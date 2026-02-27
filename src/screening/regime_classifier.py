class RegimeClassifier:

    def classify(self, state):

        net_gex = state.get("net_gex")
        iv_vs_hv = state.get("iv_vs_hv")
        surface = state.get("surface_shift_regime")

        if net_gex is None:
            return "UNKNOWN"

        if net_gex < 0:
            return "SHORT_GAMMA"

        if net_gex > 0:
            return "LONG_GAMMA"

        return "FLIP_ZONE"