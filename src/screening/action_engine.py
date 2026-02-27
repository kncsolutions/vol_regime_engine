class ActionEngine:

    def generate(self, regime, structure, state):

        spot = structure["current_spot"]
        flip = structure["gamma_flip"]
        high = structure["recent_high"]
        low = structure["recent_low"]
        call_wall = structure["call_wall"]
        put_wall = structure["put_wall"]

        if regime == "SHORT_GAMMA":

            if spot > flip:
                return {
                    "action": "LONG_ABOVE",
                    "trigger": high,
                    "stop": flip
                }

            if spot < flip:
                return {
                    "action": "SHORT_BELOW",
                    "trigger": low,
                    "stop": flip
                }

        elif regime == "LONG_GAMMA":

            return {
                "action": "MEAN_REVERT",
                "short_from": call_wall,
                "long_from": put_wall,
                "stop_short": call_wall * 1.002,
                "stop_long": put_wall * 0.998
            }

        elif regime == "FLIP_ZONE":

            return {
                "action": "BREAKOUT",
                "long_above": flip,
                "short_below": flip,
                "stop_long": flip,
                "stop_short": flip
            }

        return {"action": "NO_TRADE"}