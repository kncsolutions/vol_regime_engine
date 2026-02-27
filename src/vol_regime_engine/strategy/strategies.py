from dataclasses import dataclass
from typing import Optional


@dataclass
class StrategySignal:
    name: str
    bias: str
    rationale: str
    risk_profile: str
    conviction: float