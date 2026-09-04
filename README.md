# market.py — free market data CLI for US stocks & ETFs

A small Python command-line tool that retrieves market data without any
API key or account. Data comes from Yahoo Finance via
[yfinance](https://github.com/ranaroussi/yfinance), covering US stocks
and ETFs with historical and near-real-time quotes.

## Features

- **Quotes** — current price, change, volume, market cap, and 52-week
  range for one or many symbols at once
- **History** — OHLCV candles for daily, weekly, or intraday intervals
  (1m–3mo), printed as a table or exported to CSV
- **Indicators** — SMA, EMA, RSI, MACD, and Bollinger Bands computed on
  the fly; attach them to any history query or print the latest values

## Install

Requires Python 3.9+ and an internet connection. No API key needed.

```bash
cd market-data-tools
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

### Real-time quotes

```bash
.venv/bin/python market.py quote AAPL MSFT VTI
```

### Historical data

```bash
# last 15 trading days of AAPL as a table
.venv/bin/python market.py history AAPL --period 3mo

# full year of daily data to CSV
.venv/bin/python market.py history AAPL --period 1y --csv aapl.csv

# intraday: 5-minute bars for the last 5 days, show last 20 rows
.venv/bin/python market.py history AAPL --period 5d --interval 5m --limit 20
```

### Technical indicators

```bash
# last 15 days plus SMA(20), RSI(14), and MACD columns
.venv/bin/python market.py history AAPL --period 6mo --indicators sma:20,rsi,macd

# latest indicator values
.venv/bin/python market.py indicators SPY --period 1y
```

Indicator spec syntax: `name[:param[:param...]]` joined by commas —
`sma:20`, `ema:50`, `rsi:14`, `macd:12:26:9`, `bb:20:2` (Bollinger).
Available names: `sma`, `ema`, `rsi`, `macd`, `bb`.

## Notes & caveats

- Data is from Yahoo Finance and is intended for personal, non-commercial use.
- Quotes are near-real-time; Yahoo can throttle or delay some feeds.
- Yahoo rate-limits aggressive polling — keep request bursts modest.
- Intraday history is limited by Yahoo: 1m bars only go back ~7 days,
  longer intervals proportionally more.

## Project layout

- `market.py` — CLI entry point (argparse subcommands)
- `fetcher.py` — yfinance wrapper: history + quotes
- `indicators.py` — pandas implementations of SMA/EMA/RSI/MACD/Bollinger
- `display.py` — aligned terminal tables and number formatting helpers
