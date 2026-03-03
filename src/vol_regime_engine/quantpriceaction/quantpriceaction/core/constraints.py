import torch
import torch.nn.functional as F


class Constraints:

    # ==============================
    # Pivot Detection (Vectorized)
    # ==============================
    @staticmethod
    def pivots(price, k=3):

        price = price.unsqueeze(1)

        max_pool = F.max_pool1d(
            price,
            kernel_size=2*k+1,
            stride=1,
            padding=k
        )

        min_pool = -F.max_pool1d(
            -price,
            kernel_size=2*k+1,
            stride=1,
            padding=k
        )

        pivot_high = (price == max_pool).squeeze(1)
        pivot_low = (price == min_pool).squeeze(1)

        return pivot_high, pivot_low

    # ==============================
    # Symmetry Constraint
    # ==============================
    @staticmethod
    def symmetry(p1, p2, tol=0.03):
        return torch.abs(p1 - p2) / (p1 + 1e-8) < tol

    # ==============================
    # Higher High / Lower Low
    # ==============================
    @staticmethod
    def higher_high(p1, p2):
        return p2 > p1

    @staticmethod
    def lower_low(p1, p2):
        return p2 < p1

    # ==============================
    # Breakout
    # ==============================
    @staticmethod
    def breakout_above(price, level):
        return price > level

    @staticmethod
    def breakout_below(price, level):
        return price < level

    # ==============================
    # Volatility Compression
    # ==============================
    @staticmethod
    def compression(price, window=20):

        rolling_max = F.max_pool1d(
            price.unsqueeze(1),
            kernel_size=window,
            stride=1
        ).squeeze(1)

        rolling_min = -F.max_pool1d(
            -price.unsqueeze(1),
            kernel_size=window,
            stride=1
        ).squeeze(1)

        range_series = rolling_max - rolling_min

        return range_series[:, 1:] < range_series[:, :-1]

    # ==============================
    # Trend Slope
    # ==============================
    @staticmethod
    def slope(price, window=20):

        t = torch.arange(window, device=price.device).float()

        t = t - t.mean()

        slopes = []

        for i in range(price.shape[1] - window):
            y = price[:, i:i+window]
            y = y - y.mean(dim=1, keepdim=True)

            beta = (t * y).sum(dim=1) / (t**2).sum()
            slopes.append(beta)

        return torch.stack(slopes, dim=1)

    # ==============================
    # Structural Energy
    # ==============================
    @staticmethod
    def structural_energy(price):

        height = torch.max(price, dim=1).values - torch.min(price, dim=1).values

        atr = torch.mean(torch.abs(price[:, 1:] - price[:, :-1]), dim=1)

        return (height ** 2) / (atr + 1e-6)