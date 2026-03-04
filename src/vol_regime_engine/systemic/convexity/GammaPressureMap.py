class GammaPressureMap:

    def __init__(self, put_wall, flip, call_wall):
        self.put_wall = put_wall
        self.flip = flip
        self.call_wall = call_wall
        self.has_flip = flip is not None

    def zone(self, price):

        if not self.has_flip:
            return "ONE_SIDED_GAMMA"

        if price <= self.put_wall:
            return "PUT_SUPPORT"

        if price < self.flip:
            return "LONG_GAMMA_RANGE"

        if price <= self.call_wall:
            return "SHORT_GAMMA_RANGE"

        return "CALL_SQUEEZE"