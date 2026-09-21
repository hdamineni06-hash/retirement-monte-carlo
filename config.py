"""
Central assumptions for the retirement withdrawal Monte Carlo simulator.
All other modules import from here so scenarios can be changed in one place.
"""

# --- Portfolio ---
STARTING_PORTFOLIO = 1_000_000      # total investable assets at retirement
STOCK_ALLOCATION = 0.60             # SPY weight
BOND_ALLOCATION = 0.40              # AGG weight

# --- Timeline ---
RETIREMENT_AGE = 65
HORIZON_YEARS = 30                  # simulate ages 65 -> 94
END_AGE = RETIREMENT_AGE + HORIZON_YEARS

# --- Account structure (traditional vs. Roth withdrawal sequencing) ---
# Fraction of the starting portfolio held in each tax "bucket". A 75/25 split
# is a reasonable proxy for a career saver who leaned on a 401(k)/Trad IRA
# with a smaller Roth IRA/Roth 401(k) balance.
TRADITIONAL_FRACTION = 0.75
ROTH_FRACTION = 0.25

# Order in which accounts are tapped for discretionary (non-RMD) spending.
# "traditional_first" draws down the tax-deferred bucket first (before any
# RMDs are forced), which shrinks future RMDs; "roth_first" preserves the
# tax-deferred bucket's tax-deferred growth longest but leads to larger RMDs
# later. Either way, once RMDs start at 73 they are mandatory regardless of
# sequencing.
WITHDRAWAL_SEQUENCE = "traditional_first"  # "traditional_first" | "roth_first"

# --- Taxes ---
FEDERAL_TAX_RATE = 0.22             # flat approximation of the marginal bracket
                                     # applied to traditional withdrawals/RMDs.
                                     # State tax is ignored per assumptions.
                                     # Roth withdrawals are tax-free.

# --- RMDs (SECURE 2.0 Act) ---
RMD_START_AGE = 73

# --- Spending / inflation ---
# Withdrawal rates are expressed as a percent of the STARTING portfolio in
# year 1 (the classic "safe withdrawal rate" convention). Real dollar
# spending is then held constant by adjusting for inflation each year.
INFLATION_RATE = 0.025
WITHDRAWAL_RATE_RANGE = (0.03, 0.05)  # analyze.py sweeps this range
WITHDRAWAL_RATE_STEP = 0.0025

# --- Simulation ---
N_SIMULATIONS = 10_000
RANDOM_SEED = 42

# --- Data ---
TICKERS = {"stock": "SPY", "bond": "AGG"}
HISTORICAL_DATA_START = "2003-10-01"  # AGG inception; keeps SPY/AGG history aligned
HISTORICAL_RETURNS_CSV = "data/historical_returns.csv"
