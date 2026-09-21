"""
Monte Carlo engine for the retirement withdrawal simulation.

Each simulated path bootstraps (samples with replacement) from the observed
history of blended 60/40 SPY/AGG annual returns, rather than assuming
returns are normally distributed. Each year, a withdrawal is taken from a
traditional (tax-deferred) and a Roth (tax-free) bucket according to a
configurable sequencing rule, with Required Minimum Distributions forced
out of the traditional bucket starting at age 73 (SECURE 2.0).
"""

import numpy as np

import config
from fetch_data import fetch_historical_returns

# IRS Uniform Lifetime Table (2022 update, Pub. 590-B) used to compute RMDs.
# divisor = age -> life-expectancy factor; RMD = traditional balance / divisor.
RMD_DIVISORS = {
    73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1,
    80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2,
    87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1,
    94: 9.5, 95: 8.9, 96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8, 100: 6.4,
}
_MAX_RMD_AGE = max(RMD_DIVISORS)


def get_rmd_divisor(age: int) -> float:
    """IRS Uniform Lifetime Table divisor, clamped beyond the table's range."""
    return RMD_DIVISORS[min(age, _MAX_RMD_AGE)]


def bootstrap_return_paths(historical_returns, n_sims, n_years, rng):
    """Sample n_sims x n_years annual returns, i.i.d. with replacement, from
    the historical return series (a resampling/bootstrap approach rather
    than a parametric normal-distribution assumption)."""
    return rng.choice(historical_returns, size=(n_sims, n_years), replace=True)


def run_monte_carlo(withdrawal_rate: float, n_sims: int = None, seed: int = None):
    """
    Simulate n_sims retirements at a given first-year withdrawal rate.

    Returns a dict with:
        success_rate: fraction of paths that never fully deplete
        balances: (n_sims, n_years+1) array of year-end total portfolio value
        depletion_year: (n_sims,) array, year of depletion or -1 if it survived
    """
    n_sims = n_sims or config.N_SIMULATIONS
    n_years = config.HORIZON_YEARS
    rng = np.random.default_rng(seed if seed is not None else config.RANDOM_SEED)

    historical = fetch_historical_returns()["blended_return"].to_numpy()
    returns = bootstrap_return_paths(historical, n_sims, n_years, rng)

    trad = np.full(n_sims, config.STARTING_PORTFOLIO * config.TRADITIONAL_FRACTION)
    roth = np.full(n_sims, config.STARTING_PORTFOLIO * config.ROTH_FRACTION)

    balances = np.zeros((n_sims, n_years + 1))
    balances[:, 0] = trad + roth
    depleted = np.zeros(n_sims, dtype=bool)
    depletion_year = np.full(n_sims, -1)

    first_year_spend = config.STARTING_PORTFOLIO * withdrawal_rate
    tax_rate = config.FEDERAL_TAX_RATE

    for year in range(1, n_years + 1):
        age = config.RETIREMENT_AGE + year - 1  # age at the start of this year
        target_net_spend = first_year_spend * (1 + config.INFLATION_RATE) ** (year - 1)

        # RMD is mandatory once the account holder reaches RMD_START_AGE.
        if age >= config.RMD_START_AGE:
            rmd = trad / get_rmd_divisor(age)
        else:
            rmd = np.zeros(n_sims)

        trad_withdrawal = rmd.copy()
        roth_withdrawal = np.zeros(n_sims)
        net_from_rmd = rmd * (1 - tax_rate)
        remaining_need = target_net_spend - net_from_rmd

        if config.WITHDRAWAL_SEQUENCE == "traditional_first":
            first_bucket, second_bucket = "trad", "roth"
        else:
            first_bucket, second_bucket = "roth", "trad"

        for bucket in (first_bucket, second_bucket):
            need_mask = remaining_need > 0
            if not need_mask.any():
                break
            if bucket == "trad":
                available = np.maximum(trad - trad_withdrawal, 0)
                gross_needed = np.where(need_mask, remaining_need / (1 - tax_rate), 0)
                draw = np.minimum(gross_needed, available)
                trad_withdrawal += draw
                remaining_need -= draw * (1 - tax_rate)
            else:
                available = np.maximum(roth - roth_withdrawal, 0)
                draw = np.minimum(np.where(need_mask, remaining_need, 0), available)
                roth_withdrawal += draw
                remaining_need -= draw

        # If the RMD alone exceeds the year's spending need, the leftover
        # after-tax cash is reinvested (simplifying assumption: swept into
        # the Roth-like bucket as after-tax savings rather than spent).
        excess_rmd_cash = np.maximum(-remaining_need, 0)

        trad = np.maximum(trad - trad_withdrawal, 0)
        roth = np.maximum(roth - roth_withdrawal, 0) + excess_rmd_cash

        shortfall = remaining_need > 1e-6  # spending need not fully met this year
        newly_depleted = shortfall & ~depleted
        depletion_year[newly_depleted] = year
        depleted = depleted | shortfall

        # Grow surviving balances by this year's bootstrapped market return.
        year_return = returns[:, year - 1]
        trad = trad * (1 + year_return)
        roth = roth * (1 + year_return)

        balances[:, year] = np.where(depleted, 0.0, trad + roth)

    success_rate = 1 - depleted.mean()
    return {
        "withdrawal_rate": withdrawal_rate,
        "success_rate": success_rate,
        "balances": balances,
        "depletion_year": depletion_year,
    }


if __name__ == "__main__":
    result = run_monte_carlo(withdrawal_rate=0.04)
    print(f"4.00% withdrawal rate -> success rate: {result['success_rate']:.1%}")
    print(f"Median ending balance: ${np.median(result['balances'][:, -1]):,.0f}")
