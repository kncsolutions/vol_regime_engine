class StructureExtractor:

    def extract(self, state):

        return {
            "gamma_flip": state.get("gamma_flip"),
            "call_wall": state.get("call_wall"),
            "put_wall": state.get("put_wall"),
            "recent_high": state.get("recent_high"),
            "recent_low": state.get("recent_low"),
            "current_spot": state.get("current_spot")
        }