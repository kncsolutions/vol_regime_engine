from .gpu.engine import GPUEngine
from .patterns.registry import PatternRegistry
from .patterns.autoload import load_all_patterns

class QuantPriceAction:

    def __init__(self, device="cuda"):
        load_all_patterns()
        self.engine = GPUEngine(device=device)

    def load(self, price_array):
        self.engine.load(price_array)

    def detect(self):
        return self.engine.evaluate()
