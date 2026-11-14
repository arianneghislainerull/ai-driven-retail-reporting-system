import numpy as np
import pandas as pd
from utils import safe_div

def coerce_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c and c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def build_kpis(df: pd.DataFrame, m) -> pd.DataFrame:
    df = df.copy()
    df = coerce_numeric(df, [m.units, m.price, m.cost])
    df = df.dropna(subset=[m.units, m.price, m.cost]).copy()

    df["sales"] = df[m.units] * df[m.price]
    df["cogs"] = df[m.units] * df[m.cost]
    df["margin"] = df["sales"] - df["cogs"]
    df["margin_rate"] = safe_div(df["margin"].values, df["sales"].values)

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["margin_rate"]).copy()
    return df

def executive_snapshot(df: pd.DataFrame) -> dict:
    total_sales = float(df["sales"].sum())
    total_cogs = float(df["cogs"].sum())
    total_margin = float(df["margin"].sum())
    mr = (total_margin / total_sales) if total_sales else np.nan
    return {
        "total_sales": total_sales,
        "total_cogs": total_cogs,
        "total_margin": total_margin,
        "margin_rate": mr
    }