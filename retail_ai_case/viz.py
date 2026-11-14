import os
import pandas as pd
import matplotlib.pyplot as plt

from utils import safe_div

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_fig(out_dir: str, filename: str, dpi=220) -> str:
    ensure_dir(out_dir)
    path = os.path.join(out_dir, filename)
    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close()
    return path

def _titleize(s: str) -> str:
    return s.replace("_", " ").title()

def build_report_charts_and_captions(df: pd.DataFrame, m, report_dir: str, top_n=10, scatter_top_k=25):
    """
    Returns charts: list[dict] each with:
      title, path, caption, takeaway
    """
    ensure_dir(report_dir)
    charts = []

    def has(col): return col is not None and col in df.columns

    def agg_by(dim: str) -> pd.DataFrame:
        g = df.groupby(dim).agg(
            sales=("sales", "sum"),
            margin=("margin", "sum"),
            cogs=("cogs", "sum"),
            units=(m.units, "sum") if has(m.units) else ("sales", "count"),
        ).reset_index()
        g["margin_rate"] = safe_div(g["margin"].values, g["sales"].values)
        return g

    # --- 1) Trend charts
    if has(m.date):
        ts = df.dropna(subset=[m.date]).copy()
        ts[m.date] = pd.to_datetime(ts[m.date], errors="coerce")
        ts = ts.dropna(subset=[m.date])

        ts_m = ts.groupby(pd.Grouper(key=m.date, freq="ME")).agg(
            sales=("sales", "sum"),
            margin=("margin", "sum"),
        ).reset_index()
        ts_m["margin_rate"] = safe_div(ts_m["margin"].values, ts_m["sales"].values)

        plt.figure()
        plt.plot(ts_m[m.date], ts_m["sales"], marker="o")
        plt.title("Sales Trend (Monthly)")
        plt.xlabel("Month"); plt.ylabel("Sales")
        charts.append({
            "title": "Sales Trend (Monthly)",
            "path": save_fig(report_dir, "01_sales_trend.png"),
            "caption": "Total sales by month.",
            "takeaway": "Use this to identify seasonality and performance inflection points (promo impact, demand shifts, supply disruptions)."
        })

        plt.figure()
        plt.plot(ts_m[m.date], ts_m["margin_rate"], marker="o")
        plt.title("Margin Rate Trend (Monthly)")
        plt.xlabel("Month"); plt.ylabel("Margin Rate")
        charts.append({
            "title": "Margin Rate Trend (Monthly)",
            "path": save_fig(report_dir, "02_margin_rate_trend.png"),
            "caption": "Profitability by month (margin ÷ sales).",
            "takeaway": "If sales rise while margin rate falls, growth may be coming from discounting or cost pressure—often a bigger risk than sales alone."
        })

    # --- 2) Portfolio scatter
    scatter_dim = None
    for key in ["category", "division", "brand"]:
        col = getattr(m, key, None)
        if has(col):
            scatter_dim = col
            break

    if scatter_dim:
        g = agg_by(scatter_dim).dropna(subset=[scatter_dim, "margin_rate"]).sort_values("sales", ascending=False).head(scatter_top_k)
        sizes = (g["sales"] / g["sales"].max()) * 900 + 100

        plt.figure()
        plt.scatter(g["sales"], g["margin_rate"], s=sizes, alpha=0.75)
        plt.title(f"Portfolio: Sales vs Margin Rate ({_titleize(scatter_dim)})")
        plt.xlabel("Sales"); plt.ylabel("Margin Rate")

        label_idx = set(
            g.sort_values("sales", ascending=False).head(5).index.tolist() +
            g.sort_values("margin_rate", ascending=True).head(5).index.tolist()
        )
        for i in label_idx:
            plt.annotate(str(g.loc[i, scatter_dim]),
                         (g.loc[i, "sales"], g.loc[i, "margin_rate"]),
                         fontsize=8, xytext=(6, 6), textcoords="offset points")

        charts.append({
            "title": f"Portfolio: Sales vs Margin Rate ({_titleize(scatter_dim)})",
            "path": save_fig(report_dir, "03_portfolio_scatter.png"),
            "caption": "Each point is a segment; X=sales, Y=margin rate; size indicates relative sales.",
            "takeaway": "Bottom-right (high sales, low margin) is the best place to focus first—small improvements here can produce the biggest profit lift."
        })

    # --- 3) Top sales + worst margin
    primary_dim = None
    for key in ["division", "category", "brand", "region"]:
        col = getattr(m, key, None)
        if has(col):
            primary_dim = col
            break

    if primary_dim:
        g = agg_by(primary_dim).dropna(subset=["margin_rate"]).copy()

        top_sales = g.sort_values("sales", ascending=False).head(top_n)
        plt.figure()
        plt.barh(top_sales[primary_dim].astype(str)[::-1], top_sales["sales"][::-1])
        plt.title(f"Top {top_n} by Sales ({_titleize(primary_dim)})")
        plt.xlabel("Sales"); plt.ylabel(_titleize(primary_dim))
        charts.append({
            "title": f"Top {top_n} by Sales ({_titleize(primary_dim)})",
            "path": save_fig(report_dir, "04_top_by_sales.png"),
            "caption": "Highest-revenue segments.",
            "takeaway": "These segments drive overall results—monitor them closely and defend share/availability."
        })

        cutoff = g["sales"].quantile(0.25)
        core = g[g["sales"] >= cutoff].copy()
        worst_mr = core.sort_values("margin_rate", ascending=True).head(top_n)

        plt.figure()
        plt.barh(worst_mr[primary_dim].astype(str)[::-1], worst_mr["margin_rate"][::-1])
        plt.title(f"Worst {top_n} Margin Rate (Sales ≥ 25th pct) ({_titleize(primary_dim)})")
        plt.xlabel("Margin Rate"); plt.ylabel(_titleize(primary_dim))
        charts.append({
            "title": f"Worst {top_n} Margin Rate (Sales ≥ 25th pct) ({_titleize(primary_dim)})",
            "path": save_fig(report_dir, "05_worst_margin_rate.png"),
            "caption": "Lowest margin-rate segments among meaningful sales contributors.",
            "takeaway": "These are your margin leaks. Investigate pricing, cost, promo depth, returns/shrink, and mix for fast profit wins."
        })

    # --- 4) Region x Store Size matrix
    if has(getattr(m, "region", None)) and has(getattr(m, "store_size", None)):
        region_col = m.region
        size_col = m.store_size

        piv = df.groupby([region_col, size_col]).agg(
            sales=("sales", "sum"),
            margin=("margin", "sum")
        ).reset_index()
        piv["margin_rate"] = safe_div(piv["margin"].values, piv["sales"].values)
        pivot_mr = piv.pivot(index=region_col, columns=size_col, values="margin_rate")

        plt.figure()
        plt.imshow(pivot_mr.fillna(0).values, aspect="auto")
        plt.title("Margin Rate by Region and Store Size")
        plt.xlabel("Store Size"); plt.ylabel("Region")
        plt.xticks(range(len(pivot_mr.columns)), [str(c) for c in pivot_mr.columns], rotation=45, ha="right")
        plt.yticks(range(len(pivot_mr.index)), [str(i) for i in pivot_mr.index])
        plt.colorbar(label="Margin Rate")

        charts.append({
            "title": "Margin Rate by Region and Store Size",
            "path": save_fig(report_dir, "06_region_store_size_mr.png"),
            "caption": "Profitability differences across region + store-size combinations.",
            "takeaway": "Great for spotting execution gaps: which formats win/lose by region, and where to replicate best practices."
        })

    # --- 5) Anomalies plot
    if "is_anomaly" in df.columns:
        plt.figure()
        plt.scatter(df["sales"], df["margin_rate"], alpha=0.20)
        an = df[df["is_anomaly"] == -1]
        plt.scatter(an["sales"], an["margin_rate"], alpha=0.95)
        plt.title("Anomalies Highlighted: Sales vs Margin Rate")
        plt.xlabel("Sales"); plt.ylabel("Margin Rate")

        charts.append({
            "title": "Anomalies Highlighted: Sales vs Margin Rate",
            "path": save_fig(report_dir, "07_anomaly_scatter.png"),
            "caption": "Outliers compared to typical behavior (unusual price/cost/margin patterns).",
            "takeaway": "Prioritize high-sales anomalies—these can indicate major data issues or high-impact promo/return/shrink events."
        })

    return charts