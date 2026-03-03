from .base import BasePattern
from .registry import PatternRegistry
from ..core.constraints import Constraints
import torch


def load_all_patterns():

    PatternRegistry.register(double_top())
    PatternRegistry.register(double_bottom())
    PatternRegistry.register(ascending_triangle())
    register_bulk_variations()


# ==============================
# DOUBLE TOP
# ==============================
def double_top():

    def detect(ctx):

        ph = ctx["pivot_high"]
        price = ctx["price"]

        h1 = ph[:, :-2]
        h2 = ph[:, 1:-1]
        h3 = ph[:, 2:]

        p1 = price[:, :-2]
        p2 = price[:, 1:-1]
        p3 = price[:, 2:]

        structure = h1 & (~h2) & h3

        symmetry = Constraints.symmetry(p1, p3)

        breakout = Constraints.breakout_below(p3, p2)

        return (structure & symmetry & breakout)

    return BasePattern("DoubleTop", [detect])


# ==============================
# DOUBLE BOTTOM
# ==============================
def double_bottom():

    def detect(ctx):

        pl = ctx["pivot_low"]
        price = ctx["price"]

        l1 = pl[:, :-2]
        l2 = pl[:, 1:-1]
        l3 = pl[:, 2:]

        p1 = price[:, :-2]
        p2 = price[:, 1:-1]
        p3 = price[:, 2:]

        structure = l1 & (~l2) & l3

        symmetry = Constraints.symmetry(p1, p3)

        breakout = Constraints.breakout_above(p3, p2)

        return (structure & symmetry & breakout)

    return BasePattern("DoubleBottom", [detect])


# ==============================
# ASCENDING TRIANGLE
# ==============================
def ascending_triangle():

    def detect(ctx):

        slopes = ctx["slopes"]
        compression = ctx["compression"]

        uptrend = slopes > 0

        return uptrend[:, -1:] & compression[:, -1:]

    return BasePattern("AscendingTriangle", [detect])






# ==============================
# AUTO-GENERATE VARIATIONS
# ==============================
def register_bulk_variations():
    def high_energy_filter(ctx):
        energy = ctx["energy"]

        threshold = torch.quantile(energy, 0.75)

        return energy > threshold

    base_names = [
        "HeadAndShoulders", "InverseHeadAndShoulders",
        "TripleTop", "TripleBottom",
        "BullFlag", "BearFlag",
        "RisingWedge", "FallingWedge",
        "Gartley", "Bat", "Butterfly",
        "Accumulation", "Distribution",
        "Spring", "Upthrust"
    ]

    for name in base_names:
        PatternRegistry.register(
            BasePattern(
                name,
                constraints=[high_energy_filter],
                required_keys=["energy"]
            )
        )