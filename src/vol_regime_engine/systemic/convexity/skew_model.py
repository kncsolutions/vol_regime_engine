# systemic/convexity/skew_model.py

class SkewModel:

    def __init__(self, delta_slope, delta_curvature):
        self.delta_slope = delta_slope
        self.delta_curvature = delta_curvature

    def skew_pressure(self):

        slope_pressure = abs(self.delta_slope)
        curvature_pressure = abs(self.delta_curvature)

        return slope_pressure + curvature_pressure