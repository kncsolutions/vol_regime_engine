from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EngineState:
    # Market structure
    option_chains: Dict
    spot: float
    gamma_flip_level: float

    # Volatility
    atr_pct: float
    iv: float
    hv: float
    vol_expanding: bool

    # Flow
    futures_state: str

    # Surface
    skew_state: str
    surface_state: str

    # Cross asset
    cross_asset_raw_score: float

    # Scaling
    gex_scale: float

    # Optional fields (safe defaults)
    timestamp: Optional[str] = None