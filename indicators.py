"""Technical indicators computed with pandas — no TA-Lib required.

All functions take a pandas Series of closes and return Series aligned
to the input index. NaN where the window has not filled yet.
"""

from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return close.rolling(window=window).mean()


def ema(close: pd.Series, window: int) -> pd.Series:
    """Exponential moving average."""
    return close.ewm(span=window, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / window, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD line, signal line, and histogram."""
    line = ema(close, fast) - ema(close, slow)
    signal_line = line.ewm(span=signal, adjust=False).mean()
    return line, signal_line, line - signal_line


def bollinger(close: pd.Series, window: int = 20, num_std: float = 2.0):
    """Bollinger Bands: middle, upper, and lower."""
    mid = sma(close, window)
    std = close.rolling(window=window).std(ddof=0)
    return mid, mid + num_std * std, mid - num_std * std


# name -> default params (arg name list kept for error messages)
DEFAULTS = {
    "sma": ((20,), ["window"]),
    "ema": ((20,), ["window"]),
    "rsi": ((14,), ["window"]),
    "macd": ((12, 26, 9), ["fast", "slow", "signal"]),
    "bb": ((20, 2.0), ["window", "std"]),
}


def parse_spec(spec: str) -> list[tuple[str, tuple]]:
    """Parse an indicator spec string.

    'sma:20,rsi,macd,bb:20:2' ->
        [('sma', (20,)), ('rsi', (14,)), ('macd', (12, 26, 9)), ('bb', (20, 2.0))]
    """
    parsed: list[tuple[str, tuple]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        name, *raw = part.split(":")
        name = name.lower()
        if name not in DEFAULTS:
            raise ValueError(
                f"unknown indicator '{name}' (available: {', '.join(sorted(DEFAULTS))})"
            )
        defaults = DEFAULTS[name][0]
        params: list = []
        for i, value in enumerate(raw):
            default = defaults[i] if i < len(defaults) else None
            try:
                params.append(float(value) if isinstance(default, float) else int(value))
            except ValueError:
                raise ValueError(f"'{value}' is not a valid number for {name}") from None
        params += list(defaults[len(params):])  # fill the rest with defaults
        parsed.append((name, tuple(params)))
    return parsed


def compute(name: str, close: pd.Series, params: tuple) -> dict[str, pd.Series]:
    """Compute one indicator and return {column-name: Series}."""
    if name == "sma":
        (w,) = params
        return {f"SMA({w})": sma(close, w)}
    if name == "ema":
        (w,) = params
        return {f"EMA({w})": ema(close, w)}
    if name == "rsi":
        (w,) = params
        return {f"RSI({w})": rsi(close, w)}
    if name == "macd":
        line, sig, hist = macd(close, *params)
        return {"MACD": line, "MACD Signal": sig, "MACD Hist": hist}
    if name == "bb":
        w, k = params
        mid, upper, lower = bollinger(close, w, k)
        return {f"BB Mid({w})": mid, f"BB Upper({w})": upper, f"BB Lower({w})": lower}
    raise ValueError(f"unknown indicator '{name}'")
