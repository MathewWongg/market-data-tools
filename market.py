#!/usr/bin/env python3
"""Market data CLI for US stocks & ETFs — free, no API key required.

Data comes from Yahoo Finance through yfinance.

Examples:
  python market.py quote AAPL MSFT VTI
  python market.py history AAPL --period 6mo --indicators sma:20,rsi,macd
  python market.py history AAPL --period 1y --interval 1wk --csv aapl_weekly.csv
  python market.py indicators SPY --period 1y
"""

from __future__ import annotations

import argparse
import sys

from display import fmt_cap, fmt_num, fmt_pct, fmt_vol, table
from fetcher import MarketDataError, history, quotes
from indicators import compute, parse_spec

# Intervals whose timestamps are dates only (no intraday time).
DAILY_INTERVALS = {"1d", "5d", "1wk", "1mo", "3mo"}

# Rows shown when printing history without an explicit --limit.
DISPLAY_LIMIT = 15


def _fmt_float(value, decimals: int = 2) -> str:
    try:
        if value is None or value != value:  # None or NaN
            return "—"
    except TypeError:
        pass
    return fmt_num(value, decimals)


def cmd_quote(args: argparse.Namespace) -> int:
    symbols = [s.upper() for s in args.tickers]
    data = quotes(symbols)

    headers = ["Symbol", "Price", "Change", "%Chg", "Open", "Day High",
               "Day Low", "Volume", "Mkt Cap", "52w High", "52w Low"]
    rows = []
    for symbol in symbols:
        q = data[symbol]
        blank = ["—"] * (len(headers) - 2)
        if q is None:
            rows.append([symbol, "unknown symbol", *blank])
            continue
        if "error" in q:
            rows.append([symbol, f"error: {q['error'][:60]}", *blank])
            continue
        rows.append([
            symbol,
            fmt_num(q["price"], 2) if q["price"] is not None else "—",
            fmt_num(q["change"], 2) if q["change"] is not None else "—",
            fmt_pct(q["pct"]),
            _fmt_float(q["open"]),
            _fmt_float(q["day_high"]),
            _fmt_float(q["day_low"]),
            fmt_vol(q["volume"]),
            fmt_cap(q["market_cap"], q.get("currency") or "USD"),
            _fmt_float(q["high_52w"]),
            _fmt_float(q["low_52w"]),
        ])
    print(table(headers, rows))
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    df = history(args.ticker, args.period, args.interval)

    if args.indicators:
        for name, params in parse_spec(args.indicators):
            for column, series in compute(name, df["Close"], params).items():
                df[column] = series

    if args.csv:
        # CSV export: everything, unless the user asked for a subset.
        out = df.tail(args.limit) if args.limit else df
        out.to_csv(args.csv)
        print(f"saved {len(out)} rows -> {args.csv}")
        return 0

    limit = args.limit if args.limit is not None else DISPLAY_LIMIT
    out = df.tail(limit)

    date_fmt = "%Y-%m-%d" if args.interval in DAILY_INTERVALS else "%Y-%m-%d %H:%M"
    headers = ["Date", *out.columns.tolist()]
    rows = []
    for ts, row in out.iterrows():
        cells = [ts.strftime(date_fmt)]
        for column in out.columns:
            value = row[column]
            if column == "Volume":
                cells.append(fmt_vol(value))
            elif column == "Adj Close":
                cells.append(_fmt_float(value, 4))
            else:
                cells.append(_fmt_float(value))
        rows.append(cells)
    print(f"{args.ticker.upper()}  {args.period} {args.interval}")
    print(table(headers, rows))
    return 0


def cmd_indicators(args: argparse.Namespace) -> int:
    df = history(args.ticker, args.period, args.interval)
    spec = args.indicators or "sma:20,sma:50,ema:20,rsi,macd,bb"

    rows = [["Close", fmt_num(df["Close"].iloc[-1], 2)]]
    for name, params in parse_spec(spec):
        for column, series in compute(name, df["Close"], params).items():
            rows.append([column, _fmt_float(series.iloc[-1])])

    latest = df.index[-1].strftime("%Y-%m-%d")
    print(f"{args.ticker.upper()}  {args.period} {args.interval}  as of {latest}")
    print(table(["Indicator", "Value"], rows))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="market.py",
        description="Free market data CLI for US stocks & ETFs (Yahoo Finance via yfinance).",
        epilog=(
            "examples:\n"
            "  python market.py quote AAPL MSFT\n"
            "  python market.py history AAPL --period 6mo --indicators sma:20,rsi,macd\n"
            "  python market.py indicators SPY --period 1y\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    q = sub.add_parser("quote", help="near-real-time quotes for one or more symbols")
    q.add_argument("tickers", nargs="+", help="symbols, e.g. AAPL MSFT VTI")

    h = sub.add_parser("history", help="historical OHLCV candles")
    h.add_argument("ticker", help="symbol, e.g. AAPL")
    h.add_argument("--period", default="1y", help="1d/5d/1mo/3mo/6mo/1y/5y/max (default: 1y)")
    h.add_argument("--interval", default="1d", help="1m/5m/15m/30m/1h/1d/1wk/1mo (default: 1d)")
    h.add_argument("--limit", type=int, default=None,
                   help=f"rows to print (default: {DISPLAY_LIMIT}); CSV exports all rows unless set")
    h.add_argument("--indicators", default=None,
                   help="comma-separated, e.g. sma:20,rsi,macd,bb:20:2")
    h.add_argument("--csv", default=None, help="export full data to this CSV file")

    i = sub.add_parser("indicators", help="latest values of technical indicators")
    i.add_argument("ticker", help="symbol, e.g. AAPL")
    i.add_argument("--period", default="6mo", help="lookback used to compute indicators (default: 6mo)")
    i.add_argument("--interval", default="1d", help="bar interval (default: 1d)")
    i.add_argument("--indicators", default=None,
                   help="comma-separated spec (default: sma:20,sma:50,ema:20,rsi,macd,bb)")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "quote":
            return cmd_quote(args)
        if args.command == "history":
            return cmd_history(args)
        if args.command == "indicators":
            return cmd_indicators(args)
        raise AssertionError(f"unhandled command: {args.command}")
    except MarketDataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
