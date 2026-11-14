import os
import shutil
import pandas as pd

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def export_outputs(out_dir: str, insights: list, anoms_df: pd.DataFrame | None, fi_df: pd.DataFrame | None, yoy_df: pd.DataFrame | None):
    ensure_dir(out_dir)

    with open(os.path.join(out_dir, "executive_insights.txt"), "w", encoding="utf-8") as f:
        for i, t in enumerate(insights or [], start=1):
            f.write(f"{i}. {t}\n")

    if anoms_df is not None and len(anoms_df) > 0:
        anoms_df.head(200).to_csv(os.path.join(out_dir, "top_anomalies.csv"), index=False)

    if fi_df is not None and len(fi_df) > 0:
        fi_df.head(200).to_csv(os.path.join(out_dir, "margin_rate_driver_importance.csv"), index=False)

    if yoy_df is not None and len(yoy_df) > 0:
        yoy_df.to_csv(os.path.join(out_dir, "yoy_summary.csv"), index=False)

    zip_path = shutil.make_archive(out_dir, "zip", out_dir)
    return zip_path