"""
Sweep withdrawal rates from 3% to 5% (0.25% steps), compute the Monte Carlo
success rate at each, and render a two-panel dashboard:
  (1) success rate vs. withdrawal rate
  (2) a sample of individual simulated portfolio paths over the horizon

Run directly:
    python analyze.py
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
from simulate import run_monte_carlo

# --- Palette (validated categorical/chrome tokens) ---
BLUE = "#2a78d6"
BLUE_LIGHT_FILL = "#9ec5f4"   # sequential step ~200, for the percentile band
BLUE_FAINT = "#2a78d6"        # individual paths, drawn at low alpha
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

SAMPLE_PATH_RATE = 0.04     # withdrawal rate used for the path panel
N_SAMPLE_PATHS = 40


def sweep_withdrawal_rates() -> pd.DataFrame:
    """Run the Monte Carlo engine across WITHDRAWAL_RATE_RANGE and return a
    DataFrame of withdrawal_rate -> success_rate."""
    low, high = config.WITHDRAWAL_RATE_RANGE
    rates = np.round(np.arange(low, high + 1e-9, config.WITHDRAWAL_RATE_STEP), 4)

    rows = []
    for rate in rates:
        result = run_monte_carlo(withdrawal_rate=rate)
        rows.append({"withdrawal_rate": rate, "success_rate": result["success_rate"]})
        print(f"  {rate:.2%} withdrawal rate -> {result['success_rate']:.1%} success")

    return pd.DataFrame(rows)


def _style_axis(ax):
    ax.set_facecolor(SURFACE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.tick_params(colors=INK_MUTED, labelsize=9)
    ax.grid(True, axis="y", color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def plot_success_rate(ax, sweep_df: pd.DataFrame):
    x = sweep_df["withdrawal_rate"] * 100
    y = sweep_df["success_rate"] * 100

    ax.plot(x, y, color=BLUE, linewidth=2, marker="o", markersize=5, zorder=3)
    ax.axhline(90, color=INK_MUTED, linewidth=1, linestyle="--", zorder=2)
    ax.text(x.iloc[0], 91.5, "90% success threshold", color=INK_MUTED, fontsize=8)

    for xi, yi in zip(x, y):
        if abs((xi * 2) - round(xi * 2)) < 1e-6:  # label every 0.5% step
            ax.annotate(f"{yi:.0f}%", (xi, yi), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8, color=INK_SECONDARY)

    ax.set_xlabel("First-year withdrawal rate", color=INK_SECONDARY, fontsize=10)
    ax.set_ylabel("Success rate (30-year horizon)", color=INK_SECONDARY, fontsize=10)
    ax.set_ylim(0, 105)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{v:.2f}%" for v in x], rotation=45, ha="right")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.set_title("Success Rate vs. Withdrawal Rate", color=INK_PRIMARY,
                 fontsize=12, fontweight="bold", loc="left")


def plot_sample_paths(ax, rng):
    result = run_monte_carlo(withdrawal_rate=SAMPLE_PATH_RATE)
    balances = result["balances"]
    years = np.arange(balances.shape[1])

    sample_idx = rng.choice(balances.shape[0], size=N_SAMPLE_PATHS, replace=False)
    for idx in sample_idx:
        ax.plot(years, balances[idx] / 1_000, color=BLUE_FAINT, linewidth=0.8,
                 alpha=0.15, zorder=2)

    p10 = np.percentile(balances, 10, axis=0) / 1_000
    p90 = np.percentile(balances, 90, axis=0) / 1_000
    median = np.median(balances, axis=0) / 1_000

    ax.fill_between(years, p10, p90, color=BLUE_LIGHT_FILL, alpha=0.4, zorder=1,
                     label="10th-90th percentile")
    ax.plot(years, median, color=BLUE, linewidth=2.5, zorder=3, label="Median path")

    ax.set_xlabel("Years into retirement", color=INK_SECONDARY, fontsize=10)
    ax.set_ylabel("Portfolio value ($ thousands)", color=INK_SECONDARY, fontsize=10)
    ax.set_title(f"Sample Simulated Portfolio Paths ({SAMPLE_PATH_RATE:.2%} withdrawal rate)",
                 color=INK_PRIMARY, fontsize=12, fontweight="bold", loc="left")
    legend = ax.legend(loc="upper right", frameon=False, fontsize=9,
                        labelcolor=INK_SECONDARY)


def build_dashboard(sweep_df: pd.DataFrame, out_path: str):
    rng = np.random.default_rng(config.RANDOM_SEED)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor=SURFACE)

    plot_success_rate(axes[0], sweep_df)
    _style_axis(axes[0])
    plot_sample_paths(axes[1], rng)
    _style_axis(axes[1])

    fig.suptitle(
        f"Retirement Withdrawal Monte Carlo  |  "
        f"${config.STARTING_PORTFOLIO:,.0f} starting portfolio, "
        f"retire at {config.RETIREMENT_AGE}, {config.HORIZON_YEARS}-year horizon, "
        f"60/40 allocation, bootstrapped SPY/AGG returns ({config.N_SIMULATIONS:,} sims)",
        fontsize=10, color=INK_MUTED, y=1.02,
    )
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    print(f"\nDashboard saved to {out_path}")


if __name__ == "__main__":
    print("Sweeping withdrawal rates 3.00%-5.00% (0.25% steps)...")
    sweep_df = sweep_withdrawal_rates()

    results_csv = "output/success_rates.csv"
    os.makedirs("output", exist_ok=True)
    sweep_df.to_csv(results_csv, index=False)
    print(f"Results saved to {results_csv}")

    build_dashboard(sweep_df, "output/dashboard.png")
