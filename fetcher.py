"""Data-fetching layer.

Built on yfinance, which reads Yahoo Finance's public endpoints:
free, no API key, covers US stocks and ETFs.
"""

from __future__ import annotations

import pandas as pd
import yfinance as yf


class MarketDataError(Exception):
    """Raised when data for a symbol cannot be retrieved."""


def history(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Download OHLCV history for one symbol.

    Returns a DataFrame indexed by date with Open/High/Low/Close/Adj
    Close/Volume columns. Raises MarketDataError when Yahoo returns
    nothing (bad symbol, bad period/interval, or network trouble).
    """
    try:
        df = yf.Ticker(symbol.upper()).history(
            period=period, interval=interval, auto_adjust=False
        )
    except Exception as exc:  # yfinance raises assorted errors on bad input
        raise MarketDataError(f"could not fetch '{symbol}': {exc}") from exc

    if df is None or df.empty:
        raise MarketDataError(f"no data for '{symbol}' (bad symbol or period/interval)")

    # Drop columns that are almost always all zeros for stock/ETF queries.
    extra = [c for c in ("Dividends", "Stock Splits") if c in df.columns]
    if extra:
        df = df.drop(columns=extra)
    return df


def _get(info, *names, default=None):
    """Read the first present value from yfinance's fast_info dict."""
    for name in names:
        try:
            value = info[name]
            if value is not None:
                return value
        except (KeyError, TypeError):
            continue
    return default


def quotes(symbols: list[str]) -> dict[str, dict]:
    """Fetch near-real-time quotes for several symbols.

    Returns {symbol: quote-dict}. The dict is None when the symbol could
    not be resolved, or {"error": ...} when Yahoo returned the symbol
    but pricing it failed.
    """
    tickers = yf.Tickers(" ".join(symbols))
    result: dict[str, dict] = {}
    for symbol in symbols:
        ticker = tickers.tickers.get(symbol)
        if ticker is None:
            result[symbol] = None
            continue
        try:
            f = ticker.fast_info
            previous_close = _get(f, "previousClose", "regularMarketPreviousClose",
                                  "previous_close")
            last = _get(f, "lastPrice", "last_price")
            change = (
                None
                if (last is None or not previous_close)
                else last - previous_close
            )
            pct = (
                None
                if (change is None or not previous_close)
                else 100.0 * change / previous_close
            )
            result[symbol] = {
                "price": last,
                "change": change,
                "pct": pct,
                "open": _get(f, "open"),
                "day_high": _get(f, "dayHigh", "day_high"),
                "day_low": _get(f, "dayLow", "day_low"),
                "volume": _get(f, "lastVolume", "last_volume"),
                "market_cap": _get(f, "marketCap", "market_cap"),
                "high_52w": _get(f, "yearHigh", "fifty_two_week_high"),
                "low_52w": _get(f, "yearLow", "fifty_two_week_low"),
                "currency": _get(f, "currency"),
            }
        except Exception as exc:
            result[symbol] = {"error": str(exc)}
    return result
