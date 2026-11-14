from dataclasses import dataclass

@dataclass
class Config:
    # Output folders
    report_dir: str = "report_assets"
    outputs_dir: str = "case_outputs"

    # Anomaly detection
    anomaly_contamination: float = 0.02
    anomaly_estimators: int = 300

    # Driver model (XGBoost)
    xgb_estimators: int = 600
    xgb_lr: float = 0.05
    xgb_max_depth: int = 6
    xgb_subsample: float = 0.9
    xgb_colsample: float = 0.8
    test_size: float = 0.2
    random_state: int = 42

    # Visuals
    top_n: int = 10
    scatter_top_k: int = 25