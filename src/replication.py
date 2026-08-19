"""Reproduce auditable comparisons from Ning (2023)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .option_pricing import (
    black_scholes_price,
    crank_nicolson_price,
    explicit_fdm_price,
    monte_carlo_price,
    scaled_convection_fdm_price,
)


MATURITIES = (0.25, 0.50, 1.00)
MATURITY_LABELS = ("3M", "6M", "1Y")

PAPER_TABLES = {
    "Table 1 - call": {
        "spot": 5.0,
        "strike": 5.5,
        "paper_exact": (0.09737, 0.13606, 0.40131),
        "paper_mcfdm": (0.09543, 0.12422, 0.39892),
        "paper_cfdm": (0.06931, 0.09384, 0.23263),
        "paper_mc": (0.09464, 0.14414, 0.40262),
    },
    "Table 2 - call": {
        "spot": 7.0,
        "strike": 7.5,
        "paper_exact": (0.18895, 0.24914, 0.63791),
        "paper_mcfdm": (0.18912, 0.24970, 0.63482),
        "paper_cfdm": (0.20013, 0.25925, 0.64361),
        "paper_mc": (0.18950, 0.24967, 0.62715),
    },
    "Table 3 - labelled put": {
        "spot": 5.5,
        "strike": 5.0,
        "paper_exact": (0.63017, 0.75512, 0.96525),
        "paper_mcfdm": (0.62755, 0.75232, 0.95113),
        "paper_cfdm": (0.64112, 0.77020, 0.97613),
        "paper_mc": (0.63720, 0.75127, 0.94432),
    },
    "Table 4 - labelled put": {
        "spot": 7.5,
        "strike": 7.0,
        "paper_exact": (0.72335, 0.90583, 1.20269),
        "paper_mcfdm": (0.71845, 0.90589, 1.20127),
        "paper_cfdm": (0.74235, 0.93100, 1.21299),
        "paper_mc": (0.72013, 0.90547, 1.19943),
    },
}


def build_paper_audit() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for table, values in PAPER_TABLES.items():
        spot = float(values["spot"])
        strike = float(values["strike"])
        for maturity, maturity_label, paper_exact in zip(
            MATURITIES, MATURITY_LABELS, values["paper_exact"], strict=True
        ):
            standard_call = black_scholes_price(
                spot, strike, maturity, 0.05, 0.25, "call"
            )
            standard_put = black_scholes_price(
                spot, strike, maturity, 0.05, 0.25, "put"
            )
            call_gap = abs(standard_call - paper_exact)
            put_gap = abs(standard_put - paper_exact)
            rows.append(
                {
                    "table": table,
                    "maturity": maturity_label,
                    "spot": spot,
                    "strike": strike,
                    "paper_exact": paper_exact,
                    "standard_call": standard_call,
                    "standard_put": standard_put,
                    "call_gap": call_gap,
                    "put_gap": put_gap,
                    "closest_standard_formula": "call" if call_gap < put_gap else "put",
                }
            )
    return pd.DataFrame(rows)


def build_method_comparison(
    simulations: int = 100_000,
    seed: int = 42,
) -> pd.DataFrame:
    scenario = PAPER_TABLES["Table 1 - call"]
    rows: list[dict[str, object]] = []
    for index, (maturity, maturity_label) in enumerate(
        zip(MATURITIES, MATURITY_LABELS, strict=True)
    ):
        spot = float(scenario["spot"])
        strike = float(scenario["strike"])
        exact = black_scholes_price(spot, strike, maturity, 0.05, 0.25, "call")
        explicit = explicit_fdm_price(
            spot, strike, maturity, 0.05, 0.25, "call", 100, 1_000
        )
        crank_nicolson = crank_nicolson_price(
            spot, strike, maturity, 0.05, 0.25, "call", 100, 1_000
        )
        monte_carlo = monte_carlo_price(
            spot,
            strike,
            maturity,
            0.05,
            0.25,
            "call",
            simulations,
            seed + index,
        )

        method_values = (
            ("Analytical Black-Scholes", exact, 0.0),
            ("Explicit FDM", explicit.price, explicit.elapsed_seconds),
            ("Crank-Nicolson", crank_nicolson.price, crank_nicolson.elapsed_seconds),
            ("Monte Carlo", monte_carlo.price, monte_carlo.elapsed_seconds),
            ("Paper reported exact", scenario["paper_exact"][index], np.nan),
            ("Paper reported MCFDM", scenario["paper_mcfdm"][index], np.nan),
            ("Paper reported CFDM", scenario["paper_cfdm"][index], np.nan),
            ("Paper reported Monte Carlo", scenario["paper_mc"][index], np.nan),
        )
        for method, price, elapsed in method_values:
            rows.append(
                {
                    "maturity": maturity_label,
                    "method": method,
                    "price": float(price),
                    "absolute_error_vs_standard_bs": abs(float(price) - exact),
                    "elapsed_seconds": elapsed,
                }
            )
    return pd.DataFrame(rows)


def build_convection_sensitivity() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    spot, strike, maturity, rate, volatility = 5.0, 5.5, 0.25, 0.05, 0.25
    exact = black_scholes_price(spot, strike, maturity, rate, volatility, "call")
    for theta in (0.75, 0.90, 1.00, 1.10, 1.25):
        result = scaled_convection_fdm_price(
            spot,
            strike,
            maturity,
            rate,
            volatility,
            "call",
            asset_steps=100,
            time_steps=1_000,
            theta=theta,
        )
        rows.append(
            {
                "theta": theta,
                "price": result.price,
                "absolute_error": abs(result.price - exact),
                "elapsed_seconds": result.elapsed_seconds,
            }
        )
    return pd.DataFrame(rows)


def save_figures(
    audit: pd.DataFrame,
    comparison: pd.DataFrame,
    sensitivity: pd.DataFrame,
    figures_dir: Path,
) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    table1 = audit[audit["table"] == "Table 1 - call"]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(table1["maturity"], table1["paper_exact"], "o-", label="Paper exact")
    ax.plot(table1["maturity"], table1["standard_call"], "s-", label="Standard Black-Scholes")
    ax.set(title="Audit of Paper Table 1", xlabel="Maturity", ylabel="Call price")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "paper_table1_audit.png", dpi=180)
    plt.close(fig)

    selected = comparison[
        comparison["method"].isin(
            ["Analytical Black-Scholes", "Explicit FDM", "Crank-Nicolson", "Monte Carlo"]
        )
    ]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for method, group in selected.groupby("method", sort=False):
        ax.plot(group["maturity"], group["price"], marker="o", label=method)
    ax.set(title="Independent Method Comparison", xlabel="Maturity", ylabel="Call price")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "independent_method_comparison.png", dpi=180)
    plt.close(fig)

    independent = comparison[
        comparison["method"].isin(["Explicit FDM", "Crank-Nicolson", "Monte Carlo"])
    ]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for method, group in independent.groupby("method", sort=False):
        ax.semilogy(
            group["maturity"],
            np.maximum(group["absolute_error_vs_standard_bs"], 1e-10),
            marker="o",
            label=method,
        )
    ax.set(title="Absolute Error Against Standard Black-Scholes", xlabel="Maturity", ylabel="Absolute error (log scale)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "independent_method_errors.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(sensitivity["theta"], sensitivity["absolute_error"], "o-")
    ax.axvline(1.0, color="black", linestyle="--", label="Standard convection")
    ax.set(
        title="Paper-Inspired Convection Sensitivity",
        xlabel=r"Convection multiplier $\theta$",
        ylabel="Absolute error",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "convection_sensitivity.png", dpi=180)
    plt.close(fig)


def run_full_replication(output_dir: str | Path = "results") -> dict[str, pd.DataFrame]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audit = build_paper_audit()
    comparison = build_method_comparison()
    sensitivity = build_convection_sensitivity()

    audit.to_csv(output_dir / "paper_table_audit.csv", index=False)
    comparison.to_csv(output_dir / "method_comparison.csv", index=False)
    sensitivity.to_csv(output_dir / "convection_sensitivity.csv", index=False)
    save_figures(audit, comparison, sensitivity, output_dir / "figures")
    return {
        "audit": audit,
        "comparison": comparison,
        "sensitivity": sensitivity,
    }
