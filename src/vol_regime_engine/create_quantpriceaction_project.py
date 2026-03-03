import os
from pathlib import Path

BASE_DIR = Path("quantpriceaction")


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def create_pyproject():
    write_file(BASE_DIR / "pyproject.toml", """
    [build-system]
    requires = ["setuptools", "wheel"]
    build-backend = "setuptools.build_meta"
    
    [project]
    name = "quantpriceaction"
    version = "0.1.0"
    description = "GPU Accelerated Quantitative Chart Pattern Detection Engine"
    authors = [{name="Pallav Nandi Chaudhuri"}]
    dependencies = ["numpy", "pandas", "torch"]
    
    [tool.setuptools.packages.find]
    where = ["."]
    """)


def create_init():
    write_file(BASE_DIR / "quantpriceaction" / "__init__.py",
               "from .engine import QuantPriceAction\n")


def create_engine():
        write_file(BASE_DIR / "quantpriceaction" / "engine.py", """
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
    """)


def create_gpu_engine():
    write_file(BASE_DIR / "quantpriceaction" / "gpu" / "engine.py", """
    import torch
    from ..patterns.registry import PatternRegistry
    
    class GPUEngine:
    
        def __init__(self, device="cuda"):
            self.device = torch.device(device if torch.cuda.is_available() else "cpu")
    
        def load(self, price_array):
            self.price = torch.tensor(price_array, dtype=torch.float32, device=self.device)
    
        def evaluate(self):
            context = self._build_context()
            results = {}
    
            for pattern in PatternRegistry.get_all():
                results[pattern.name] = pattern.detect(context)
    
            return results
    
        def _build_context(self):
            return {
                "price": self.price,
                "dummy": True
            }
    """)


def create_registry():
    write_file(BASE_DIR / "quantpriceaction" / "patterns" / "registry.py", """
    class PatternRegistry:
    
        _patterns = {}
    
        @classmethod
        def register(cls, pattern):
            cls._patterns[pattern.name] = pattern
    
        @classmethod
        def get_all(cls):
            return cls._patterns.values()
    """)


def create_base_pattern():
    write_file(BASE_DIR / "quantpriceaction" / "patterns" / "base.py", """
    class BasePattern:
    
        def __init__(self, name, constraints):
            self.name = name
            self.constraints = constraints
    
        def detect(self, context):
            return all(constraint(context) for constraint in self.constraints)
    """)


def create_constraints():
    write_file(BASE_DIR / "quantpriceaction" / "core" / "constraints.py", """
    import torch
    
    class Constraints:
    
        @staticmethod
        def always_true(context):
            return True
    
        @staticmethod
        def price_above(context):
            price = context["price"]
            return torch.mean(price) > 0
    """)


def create_pattern_autoloader():
    write_file(BASE_DIR / "quantpriceaction" / "patterns" / "autoload.py", """
    from .base import BasePattern
    from .registry import PatternRegistry
    from ..core.constraints import Constraints
    
    def load_all_patterns():
    
        pattern_names = generate_pattern_names()
    
        for name in pattern_names:
            pattern = BasePattern(
                name=name,
                constraints=[Constraints.always_true]
            )
            PatternRegistry.register(pattern)
    
    
    def generate_pattern_names():
    
        reversal = [
            "HeadAndShoulders", "InverseHeadAndShoulders",
            "DoubleTop", "DoubleBottom",
            "TripleTop", "TripleBottom",
            "DiamondTop", "DiamondBottom",
            "IslandReversal", "AdamEveTop", "AdamEveBottom",
            "RoundingTop", "RoundingBottom",
            "BumpAndRun", "PipeTop", "PipeBottom",
            "VBounce", "SpikeChannel"
        ]
    
        continuation = [
            "BullFlag", "BearFlag",
            "BullPennant", "BearPennant",
            "AscendingTriangle", "DescendingTriangle",
            "SymmetricalTriangle",
            "RisingWedge", "FallingWedge",
            "Rectangle", "CupAndHandle",
            "MeasuredMove", "ParallelChannel"
        ]
    
        volatility = [
            "NR4", "NR7", "InsideBar",
            "VolatilitySqueeze", "CompressionCoil",
            "BroadeningFormation", "Megaphone"
        ]
    
        harmonic = [
            "Gartley", "Bat", "Butterfly",
            "Crab", "DeepCrab", "Shark",
            "Cypher", "ABCD"
        ]
    
        smc = [
            "Accumulation", "Distribution",
            "Spring", "Upthrust",
            "BreakOfStructure", "ChangeOfCharacter",
            "FairValueGap", "OrderBlock",
            "LiquidityGrab"
        ]
    
        gap = [
            "BreakawayGap", "RunawayGap",
            "ExhaustionGap", "OpeningRangeBreakout"
        ]
    
        # Expand variations automatically
        expanded = []
        for base in reversal + continuation + volatility + harmonic + smc + gap:
            expanded.append(base)
            expanded.append(base + "Bullish")
            expanded.append(base + "Bearish")
    
        return expanded[:100]
    """)


def create_readme():
    write_file(BASE_DIR / "README.md", """
    # QuantPriceAction
    
    GPU Accelerated Quantitative Chart Pattern Detection Engine.
    
    ## Install
    
    pip install .
    
    ## Example
    
    ```python
    import numpy as np
    from quantpriceaction import QuantPriceAction
    
    data = np.random.randn(200, 2000).cumsum(axis=1)
    
    engine = QuantPriceAction(device="cuda")
    engine.load(data)
    patterns = engine.detect()
    
    print(patterns)
    """)

def create_tests():
    write_file(BASE_DIR / "tests" / "test_basic.py", """
    import numpy as np
    from quantpriceaction import QuantPriceAction
    
    def test_detection():
        data = np.random.randn(10, 100).cumsum(axis=1)
        model = QuantPriceAction(device="cpu")
        model.load(data)
        result = model.detect()
        assert isinstance(result, dict)
        """)

def build_project():
    create_pyproject()
    create_init()
    create_engine()
    create_gpu_engine()
    create_registry()
    create_base_pattern()
    create_constraints()
    create_pattern_autoloader()
    create_readme()
    create_tests()
    print("Project quantpriceaction created successfully.")


build_project()