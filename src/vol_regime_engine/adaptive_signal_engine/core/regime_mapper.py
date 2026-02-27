def normalize_regime(surface_regime: str) -> str:
    """
    Maps gamma_surface_regime output
    to adaptive_signal_engine decision regimes.
    """

    mapping = {
        "LONG_GAMMA_SURFACE": "long_gamma",
        "SHORT_GAMMA_SURFACE": "short_gamma",
        "MIXED_SURFACE": "flip_zone",
    }

    return mapping.get(surface_regime, "flip_zone")