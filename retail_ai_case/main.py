import argparse
import os
from datetime import datetime

from config import Config
from io_utils import load_excel
from mapping import auto_map, validate_mapping, pretty_print_mapping
from kpi import build_kpis, executive_snapshot
from analysis import (
    dims_available, breakdown, yoy_summary,
    anomaly_detection, driver_model_margin_rate, generate_exec_insights
)
from viz import build_report_charts_and_captions
from report import build_pdf
from exporter import export_outputs
from utils import money


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", required=True, help="Path to Excel dataset")
    parser.add_argument("--pdf", default="Retail_Case_Report.pdf", help="Output PDF filename")
    args = parser.parse_args()

    cfg = Config()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    print("✅ Starting pipeline")
    print("Excel:", os.path.abspath(args.excel))
    print("PDF  :", os.path.abspath(args.pdf))

    # Load
    df = load_excel(args.excel)
    print("Loaded df:", df.shape)

    # Mapping
    m = auto_map(df.columns.tolist())
    pretty_print_mapping(m)
    validate_mapping(m)

    # KPIs
    df_kpi = build_kpis(df, m)
    print("After KPI build:", df_kpi.shape)

    snapshot = executive_snapshot(df_kpi)
    print("Snapshot:",
          "Sales", money(snapshot["total_sales"]),
          "| Margin", money(snapshot["total_margin"]),
          "| MR", f"{snapshot['margin_rate']:.2%}")

    dims = dims_available(df_kpi, m)
    yoy = yoy_summary(df_kpi, m)

    # Anomalies
    df_anom, anoms = anomaly_detection(
        df_kpi, m,
        contamination=cfg.anomaly_contamination,
        n_estimators=cfg.anomaly_estimators,
        random_state=cfg.random_state
    )
    print("Anomalies found:", len(anoms))

    # Driver model (XGBoost)
    _, fi, model_metrics = driver_model_margin_rate(df_anom, m, cfg)
    print("Driver model metrics:", model_metrics)

    # Exec insights
    insights = generate_exec_insights(df_anom, m, snapshot, yoy=yoy, anoms=anoms, dims=dims)
    print("\nTop insights:")
    for i, t in enumerate(insights[:8], start=1):
        print(f"{i}. {t}")

    # Breakdown tables
    dim_tables = []
    for key, title in [("division", "Division"), ("category", "Category"), ("region", "Region"), ("brand", "Brand")]:
        col = getattr(m, key, None)
        if col and col in df_anom.columns:
            _, top_sales, worst_mr = breakdown(df_anom, m, col, top_n=cfg.top_n)

            top_sales = top_sales.copy()
            worst_mr = worst_mr.copy()
            for c in ["sales", "margin", "cogs"]:
                if c in top_sales.columns: top_sales[c] = top_sales[c].map(lambda x: f"{x:,.0f}")
                if c in worst_mr.columns: worst_mr[c] = worst_mr[c].map(lambda x: f"{x:,.0f}")
            if "margin_rate" in top_sales.columns: top_sales["margin_rate"] = top_sales["margin_rate"].map(lambda x: f"{x:.1%}")
            if "margin_rate" in worst_mr.columns: worst_mr["margin_rate"] = worst_mr["margin_rate"].map(lambda x: f"{x:.1%}")

            dim_tables.append((title, top_sales, worst_mr))

    # Anomaly table for report
    anom_table = None
    if len(anoms) > 0:
        cols = [c for c in [
            getattr(m, "division", None),
            getattr(m, "category", None),
            getattr(m, "brand", None),
            getattr(m, "region", None),
            "sales", "margin", "margin_rate"
        ] if c and c in anoms.columns]
        anom_table = anoms[cols].head(12).copy()
        if "sales" in anom_table.columns: anom_table["sales"] = anom_table["sales"].map(lambda x: f"{x:,.0f}")
        if "margin" in anom_table.columns: anom_table["margin"] = anom_table["margin"].map(lambda x: f"{x:,.0f}")
        if "margin_rate" in anom_table.columns: anom_table["margin_rate"] = anom_table["margin_rate"].map(lambda x: f"{x:.1%}")

    # Driver importance table
    driver_table = None
    if fi is not None and len(fi) > 0:
        driver_table = fi.head(15).copy()
        driver_table["importance"] = driver_table["importance"].map(lambda x: f"{x:.4f}")

    # Charts + interpretations
    charts = build_report_charts_and_captions(
        df=df_anom,
        m=m,
        report_dir=cfg.report_dir,
        top_n=cfg.top_n,
        scatter_top_k=cfg.scatter_top_k
    )
    print("Charts generated:", len(charts))

    # PDF
    build_pdf(
        pdf_path=args.pdf,
        snapshot=snapshot,
        insights=insights,
        charts=charts,
        dim_tables=dim_tables,
        anom_table=anom_table,
        driver_table=driver_table,
        generated_at=generated_at
    )
    print("✅ PDF created:", args.pdf)

    # Exports
    zip_path = export_outputs(cfg.outputs_dir, insights, anoms, fi, yoy)
    print("✅ Outputs zip:", zip_path)


if __name__ == "__main__":
    main()