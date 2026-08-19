import numpy as np

from src.option_pricing import (
    black_scholes_price,
    crank_nicolson_price,
    explicit_fdm_price,
    monte_carlo_price,
)


def test_put_call_parity() -> None:
    spot, strike, maturity, rate, volatility = 100.0, 105.0, 1.0, 0.04, 0.20
    call = black_scholes_price(spot, strike, maturity, rate, volatility, "call")
    put = black_scholes_price(spot, strike, maturity, rate, volatility, "put")
    expected = spot - strike * np.exp(-rate * maturity)
    assert abs((call - put) - expected) < 1e-10


def test_fdm_methods_match_analytical_benchmark() -> None:
    arguments = (5.0, 5.5, 0.25, 0.05, 0.25, "call")
    exact = black_scholes_price(*arguments)
    explicit = explicit_fdm_price(*arguments, asset_steps=100, time_steps=1_000)
    crank_nicolson = crank_nicolson_price(*arguments, asset_steps=100, time_steps=1_000)
    assert abs(explicit.price - exact) < 5e-4
    assert abs(crank_nicolson.price - exact) < 5e-4


def test_monte_carlo_confidence_interval_contains_exact_price() -> None:
    arguments = (5.0, 5.5, 0.25, 0.05, 0.25, "call")
    exact = black_scholes_price(*arguments)
    result = monte_carlo_price(*arguments, simulations=200_000, seed=42)
    assert result.ci95_low <= exact <= result.ci95_high


def test_call_price_increases_with_spot() -> None:
    low = black_scholes_price(90.0, 100.0, 1.0, 0.03, 0.20, "call")
    high = black_scholes_price(110.0, 100.0, 1.0, 0.03, 0.20, "call")
    assert high > low
