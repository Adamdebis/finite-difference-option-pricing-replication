"""Transparent reference implementations for European option pricing.

The scaled-convection routine is a sensitivity implementation inspired by
Ning (2023). It is deliberately not presented as an exact implementation of
the paper's MCFDM because the paper does not define all flux operators or the
function alpha(S) sufficiently to reconstruct the published algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Literal

import numpy as np
from scipy.linalg import solve_banded
from scipy.stats import norm

OptionType = Literal["call", "put"]


@dataclass(frozen=True)
class PriceResult:
    price: float
    elapsed_seconds: float
    asset_grid: np.ndarray | None = None
    value_grid: np.ndarray | None = None


@dataclass(frozen=True)
class MonteCarloResult:
    price: float
    standard_error: float
    ci95_low: float
    ci95_high: float
    elapsed_seconds: float
    simulations: int


def _validate_inputs(
    spot: float,
    strike: float,
    maturity: float,
    volatility: float,
    option_type: OptionType,
) -> None:
    if spot <= 0 or strike <= 0:
        raise ValueError("spot and strike must be positive")
    if maturity < 0:
        raise ValueError("maturity cannot be negative")
    if volatility <= 0:
        raise ValueError("volatility must be positive")
    if option_type not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'")


def black_scholes_price(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    option_type: OptionType = "call",
) -> float:
    """Return the analytical Black-Scholes price of a European option."""
    _validate_inputs(spot, strike, maturity, volatility, option_type)
    if maturity == 0:
        return float(max(spot - strike, 0.0) if option_type == "call" else max(strike - spot, 0.0))

    root_t = np.sqrt(maturity)
    d1 = (
        np.log(spot / strike)
        + (rate + 0.5 * volatility**2) * maturity
    ) / (volatility * root_t)
    d2 = d1 - volatility * root_t

    if option_type == "call":
        return float(
            spot * norm.cdf(d1)
            - strike * np.exp(-rate * maturity) * norm.cdf(d2)
        )
    return float(
        strike * np.exp(-rate * maturity) * norm.cdf(-d2)
        - spot * norm.cdf(-d1)
    )


def monte_carlo_price(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    option_type: OptionType = "call",
    simulations: int = 100_000,
    seed: int = 42,
) -> MonteCarloResult:
    """Price a European option by risk-neutral Monte Carlo.

    Antithetic normal draws reduce sampling noise while preserving a fully
    reproducible result through the explicit random seed.
    """
    _validate_inputs(spot, strike, maturity, volatility, option_type)
    if simulations < 2:
        raise ValueError("simulations must be at least 2")

    started = perf_counter()
    rng = np.random.default_rng(seed)
    pairs = simulations // 2
    z = rng.standard_normal(pairs)
    draws = np.concatenate((z, -z))
    if simulations % 2:
        draws = np.concatenate((draws, rng.standard_normal(1)))

    terminal_spot = spot * np.exp(
        (rate - 0.5 * volatility**2) * maturity
        + volatility * np.sqrt(maturity) * draws
    )
    if option_type == "call":
        payoff = np.maximum(terminal_spot - strike, 0.0)
    else:
        payoff = np.maximum(strike - terminal_spot, 0.0)

    discounted = np.exp(-rate * maturity) * payoff
    price = float(np.mean(discounted))
    standard_error = float(np.std(discounted, ddof=1) / np.sqrt(simulations))
    elapsed = perf_counter() - started
    margin = 1.96 * standard_error
    return MonteCarloResult(
        price=price,
        standard_error=standard_error,
        ci95_low=price - margin,
        ci95_high=price + margin,
        elapsed_seconds=elapsed,
        simulations=simulations,
    )


def _boundary_values(
    strike: float,
    rate: float,
    tau: float,
    s_max: float,
    option_type: OptionType,
) -> tuple[float, float]:
    discount = np.exp(-rate * tau)
    if option_type == "call":
        return 0.0, float(s_max - strike * discount)
    return float(strike * discount), 0.0


def explicit_fdm_price(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    option_type: OptionType = "call",
    asset_steps: int = 100,
    time_steps: int = 1_000,
    s_max: float | None = None,
    convection_scale: float = 1.0,
) -> PriceResult:
    """Price a European option with an explicit finite-difference grid.

    ``convection_scale`` multiplies only the r*S*dV/dS term. The standard
    Black-Scholes scheme is obtained with ``convection_scale=1``.
    """
    _validate_inputs(spot, strike, maturity, volatility, option_type)
    if asset_steps < 3 or time_steps < 1:
        raise ValueError("asset_steps >= 3 and time_steps >= 1 are required")
    if convection_scale <= 0:
        raise ValueError("convection_scale must be positive")
    if maturity == 0:
        payoff = max(spot - strike, 0.0) if option_type == "call" else max(strike - spot, 0.0)
        return PriceResult(float(payoff), 0.0)

    started = perf_counter()
    s_max = float(s_max or 4.0 * max(spot, strike))
    dt = maturity / time_steps
    asset_grid = np.linspace(0.0, s_max, asset_steps + 1)
    if option_type == "call":
        values = np.maximum(asset_grid - strike, 0.0)
    else:
        values = np.maximum(strike - asset_grid, 0.0)

    i = np.arange(1, asset_steps, dtype=float)
    convection = convection_scale * rate * i
    diffusion = volatility**2 * i**2
    a = 0.5 * dt * (diffusion - convection)
    b = 1.0 - dt * (diffusion + rate)
    c = 0.5 * dt * (diffusion + convection)

    min_weight = float(min(np.min(a), np.min(b), np.min(c)))
    if min_weight < -1e-12:
        raise ValueError(
            "Explicit grid is unstable for these settings; increase time_steps "
            f"or reduce convection_scale (minimum weight={min_weight:.3e})."
        )

    for step in range(time_steps):
        previous = values.copy()
        values[1:asset_steps] = (
            a * previous[0 : asset_steps - 1]
            + b * previous[1:asset_steps]
            + c * previous[2 : asset_steps + 1]
        )
        tau = (step + 1) * dt
        values[0], values[-1] = _boundary_values(
            strike, rate, tau, s_max, option_type
        )

    price = float(np.interp(spot, asset_grid, values))
    return PriceResult(
        price=price,
        elapsed_seconds=perf_counter() - started,
        asset_grid=asset_grid,
        value_grid=values,
    )


def scaled_convection_fdm_price(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    option_type: OptionType = "call",
    asset_steps: int = 100,
    time_steps: int = 1_000,
    s_max: float | None = None,
    theta: float = 1.0,
) -> PriceResult:
    """Paper-inspired sensitivity scheme that scales the convection term.

    This function operationalises the paper's qualitative idea of weakening or
    enhancing convection. It is not claimed as an exact MCFDM reconstruction.
    """
    return explicit_fdm_price(
        spot=spot,
        strike=strike,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
        option_type=option_type,
        asset_steps=asset_steps,
        time_steps=time_steps,
        s_max=s_max,
        convection_scale=theta,
    )


def crank_nicolson_price(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    option_type: OptionType = "call",
    asset_steps: int = 100,
    time_steps: int = 1_000,
    s_max: float | None = None,
) -> PriceResult:
    """Price a European option with the Crank-Nicolson finite-difference method."""
    _validate_inputs(spot, strike, maturity, volatility, option_type)
    if asset_steps < 3 or time_steps < 1:
        raise ValueError("asset_steps >= 3 and time_steps >= 1 are required")
    if maturity == 0:
        payoff = max(spot - strike, 0.0) if option_type == "call" else max(strike - spot, 0.0)
        return PriceResult(float(payoff), 0.0)

    started = perf_counter()
    s_max = float(s_max or 4.0 * max(spot, strike))
    dt = maturity / time_steps
    asset_grid = np.linspace(0.0, s_max, asset_steps + 1)
    if option_type == "call":
        values = np.maximum(asset_grid - strike, 0.0)
    else:
        values = np.maximum(strike - asset_grid, 0.0)

    i = np.arange(1, asset_steps, dtype=float)
    lower_operator = 0.5 * (volatility**2 * i**2 - rate * i)
    diagonal_operator = -(volatility**2 * i**2 + rate)
    upper_operator = 0.5 * (volatility**2 * i**2 + rate * i)

    interior_count = asset_steps - 1
    lhs = np.zeros((3, interior_count))
    lhs[0, 1:] = -0.5 * dt * upper_operator[:-1]
    lhs[1, :] = 1.0 - 0.5 * dt * diagonal_operator
    lhs[2, :-1] = -0.5 * dt * lower_operator[1:]

    for step in range(time_steps):
        previous = values.copy()
        rhs = (
            0.5 * dt * lower_operator * previous[0 : asset_steps - 1]
            + (1.0 + 0.5 * dt * diagonal_operator) * previous[1:asset_steps]
            + 0.5 * dt * upper_operator * previous[2 : asset_steps + 1]
        )

        tau = (step + 1) * dt
        lower_boundary, upper_boundary = _boundary_values(
            strike, rate, tau, s_max, option_type
        )
        rhs[0] -= (-0.5 * dt * lower_operator[0]) * lower_boundary
        rhs[-1] -= (-0.5 * dt * upper_operator[-1]) * upper_boundary

        values[1:asset_steps] = solve_banded((1, 1), lhs, rhs)
        values[0] = lower_boundary
        values[-1] = upper_boundary

    price = float(np.interp(spot, asset_grid, values))
    return PriceResult(
        price=price,
        elapsed_seconds=perf_counter() - started,
        asset_grid=asset_grid,
        value_grid=values,
    )
