import re
import numpy as np

def clean_col(c: str) -> str:
    c = str(c).strip()
    c = re.sub(r"\s+", "_", c)
    c = re.sub(r"[^\w_]", "", c)
    return c.lower()

def money(x) -> str:
    try:
        x = float(x)
    except Exception:
        return "—"
    ax = abs(x)
    if ax >= 1e9: return f"${x/1e9:.2f}B"
    if ax >= 1e6: return f"${x/1e6:.2f}M"
    if ax >= 1e3: return f"${x/1e3:.2f}K"
    return f"${x:,.0f}"

def pct(x) -> str:
    try:
        return f"{float(x):.2%}"
    except Exception:
        return "—"

def safe_div(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    out = np.full_like(a, np.nan, dtype=float)
    mask = b != 0
    out[mask] = a[mask] / b[mask]
    return out