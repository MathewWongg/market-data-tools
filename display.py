"""Terminal output helpers: aligned tables and number formatting."""

from __future__ import annotations

import math


def _is_number(text: str) -> bool:
    text = text.replace(",", "").replace("%", "").replace("$", "")
    for suffix in ("T", "B", "M", "K"):
        if text.endswith(suffix):
            text = text[:-1]
            break
    try:
        float(text)
        return True
    except ValueError:
        return False


def table(headers: list[str], rows: list[list[str]]) -> str:
    """Render an aligned text table; numeric columns are right-aligned."""
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    numeric = []
    for i in range(len(headers)):
        cells = [str(row[i]) for row in rows]
        numeric.append(bool(cells) and all(_is_number(c) or c == "—" for c in cells))

    def cell(text, i):
        text = str(text)
        return text.rjust(widths[i]) if numeric[i] else text.ljust(widths[i])

    lines = ["  ".join(cell(h, i) for i, h in enumerate(headers))]
    lines.append("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        lines.append("  ".join(cell(c, i) for i, c in enumerate(row)))
    return "\n".join(lines)


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def fmt_num(value, decimals: int = 2) -> str:
    if _is_blank(value):
        return "—"
    return f"{value:,.{decimals}f}"


def fmt_pct(value) -> str:
    if _is_blank(value):
        return "—"
    return f"{value:+.2f}%"


def fmt_vol(value) -> str:
    """1,234,567 -> '1.23M'."""
    if _is_blank(value):
        return "—"
    for divisor, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= divisor:
            return f"{value / divisor:,.2f}{suffix}"
    return f"{value:,.0f}"


def fmt_cap(value, currency: str = "USD") -> str:
    """3.45e12 -> 'USD 3.45T'."""
    if _is_blank(value):
        return "—"
    for divisor, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(value) >= divisor:
            return f"{currency} {value / divisor:,.2f}{suffix}"
    return f"{currency} {value:,.0f}"
