"""
Pull historical SPY and AGG total-return data via yfinance and build the
blended 60/40 annual return series that simulate.py bootstraps from.

Run directly to (re)download and cache the data:
    python fetch_data.py
"""

import datetime as dt
import os

import pandas as pd
import yfinance as yf

import config


def _download_annual_returns(ticker: str, start: str) -> pd.Series:
    """Download daily auto-adjusted close prices and convert to annual
    (calendar-year) total returns. The current, still-in-progress calendar
    year is dropped so a partial year is never treated as a full-year
    return."""
    data = yf.download(
        ticker, start=start, auto_adjust=True, progress=False
    )
    if data.empty:
        raise RuntimeError(f"No data returned for {ticker}")

    close = data["Close"][ticker]
    annual_price = close.resample("YE").last()
    annual_return = annual_price.pct_change().dropna()
    annual_return.index = annual_return.index.year
    return annual_return[annual_return.index < dt.date.today().year]


def fetch_historical_returns(force_refresh: bool = False) -> pd.DataFrame:
    """Return a DataFrame indexed by year with spy_return, agg_return, and
    blended_return (60/40, rebalanced annually) columns. Caches to CSV so
    repeated runs don't re-hit the network."""
    if not force_refresh and os.path.exists(config.HISTORICAL_RETURNS_CSV):
        return pd.read_csv(config.HISTORICAL_RETURNS_CSV, index_col="year")

    spy = _download_annual_returns(config.TICKERS["stock"], config.HISTORICAL_DATA_START)
    agg = _download_annual_returns(config.TICKERS["bond"], config.HISTORICAL_DATA_START)

    df = pd.DataFrame({"spy_return": spy, "agg_return": agg}).dropna()
    df["blended_return"] = (
        config.STOCK_ALLOCATION * df["spy_return"]
        + config.BOND_ALLOCATION * df["agg_return"]
    )
    df.index.name = "year"

    os.makedirs(os.path.dirname(config.HISTORICAL_RETURNS_CSV), exist_ok=True)
    df.to_csv(config.HISTORICAL_RETURNS_CSV)
    return df


if __name__ == "__main__":
    returns = fetch_historical_returns(force_refresh=True)
    print(f"Fetched {len(returns)} annual returns "
          f"({returns.index.min()}-{returns.index.max()})")
    print(returns.describe())
    print(f"\nSaved to {config.HISTORICAL_RETURNS_CSV}")
