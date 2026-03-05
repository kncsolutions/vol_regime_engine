import numpy as np


def dealer_pressure(row):

    gamma = row.get("gamma_score", 0)
    accel = row.get("acceleration_probability", 0)

    return gamma * accel


def simulate_hedging(spot, gamma_exposure, steps=20):

    prices = [spot]

    for _ in range(steps):

        move = np.random.normal(0, 0.3)

        hedge_flow = gamma_exposure * move

        spot += move + hedge_flow * 0.0001

        prices.append(spot)

    return prices