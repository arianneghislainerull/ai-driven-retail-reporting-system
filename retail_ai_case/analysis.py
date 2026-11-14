import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from xgboost import XGBRegressor

from utils import safe_div


def dims_available(df: pd.DataFrame, m):
    out = []
    for key in ["division", "category", "brand", "region"]:
        col = getattr(m, key, None)
        if col and col in df.columns:
            out.append(col)
    return out


def breakdown(df: pd.DataFrame, m, dim: str, top_n: int = 10):
    g = df.groupby(dim).agg(
        sales=("sales","sum"),
        cogs=("cogs","sum"),
        margin=("margin","sum"),
        units=(m.units,"sum")
    ).reset_index()
    g["margin_rate"] = safe_div(g["margin"].values, g["sales"].values)

    top_sales = g.sort_values("sales", ascending=False).head(top_n).copy()
    cutoff = g["sales"].quantile(0.25)
    worst_mr = g[g["sales"] >= cutoff].sort_values("margin_rate", ascending=True).head(top_n).copy()
    return g, top_sales, worst_mr


def yoy_summary(df: pd.DataFrame, m):
    if not (m.year and m.year in df.columns):
        return None

    y = df.groupby(m.year).agg(
        sales=("sales","sum"),
        cogs=("cogs","sum"),
        margin=("margin","sum"),
    ).reset_index().sort_values(m.year)

    y["margin_rate"] = safe_div(y["margin"].values, y["sales"].values)
    y["sales_yoy_pct"] = y["sales"].pct_change()
    y["margin_yoy_pct"] = y["margin"].pct_change()
    y["mr_change_bps"] = (y["margin_rate"].diff() * 10000.0)
    return y


def anomaly_detection(df: pd.DataFrame, m, contamination=0.02, n_estimators=300, random_state=42):
    df = df.copy()
    num_features = ["sales","cogs","margin","margin_rate", m.units, m.price, m.cost]
    num_features = [c for c in num_features if c and c in df.columns]

    iso = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state
    )
    iso.fit(df[num_features])

    df["anomaly_score"] = iso.decision_function(df[num_features])
    df["is_anomaly"] = iso.predict(df[num_features])  # -1 anomaly

    anoms = df[df["is_anomaly"] == -1].copy().sort_values("anomaly_score")
    return df, anoms


def driver_model_margin_rate(df: pd.DataFrame, m, cfg):
    target = "margin_rate"

    cat_features = []
    for key in ["division","category","brand","region","store","store_size"]:
        col = getattr(m, key, None)
        if col and col in df.columns:
            cat_features.append(col)

    num_feats = []
    for key in ["year","month","quarter"]:
        col = getattr(m, key, None)
        if col and col in df.columns:
            num_feats.append(col)

    for c in [m.price, m.cost]:
        if c and c in df.columns:
            num_feats.append(c)

    cat_features = list(dict.fromkeys(cat_features))
    num_feats = list(dict.fromkeys(num_feats))
    features = cat_features + num_feats

    model_df = df.dropna(subset=[target] + features).copy()
    X = model_df[features]
    y = model_df[target]

    preprocess = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
            ("num", "passthrough", num_feats),
        ]
    )

    reg = XGBRegressor(
        n_estimators=cfg.xgb_estimators,
        learning_rate=cfg.xgb_lr,
        max_depth=cfg.xgb_max_depth,
        subsample=cfg.xgb_subsample,
        colsample_bytree=cfg.xgb_colsample,
        random_state=cfg.random_state,
        n_jobs=-1
    )

    pipe = Pipeline(steps=[("prep", preprocess), ("model", reg)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=cfg.test_size, random_state=cfg.random_state
    )
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)

    mae = mean_absolute_error(y_test, pred)
    r2 = r2_score(y_test, pred)

    feat_names = []
    if len(cat_features) > 0:
        ohe = pipe.named_steps["prep"].named_transformers_["cat"]
        feat_names.extend(ohe.get_feature_names_out(cat_features).tolist())
    feat_names.extend(num_feats)

    importances = pipe.named_steps["model"].feature_importances_
    fi = pd.DataFrame({"feature": feat_names, "importance": importances}).sort_values("importance", ascending=False)

    metrics = {"mae": float(mae), "r2": float(r2)}
    return pipe, fi, metrics


def generate_exec_insights(df: pd.DataFrame, m, snapshot: dict, yoy=None, anoms=None, dims=None):
    insights = []

    def money_local(x):
        ax = abs(x)
        if ax >= 1e9: return f"${x/1e9:.2f}B"
        if ax >= 1e6: return f"${x/1e6:.2f}M"
        if ax >= 1e3: return f"${x/1e3:.2f}K"
        return f"${x:,.0f}"

    insights.append(
        f"Overall margin rate is {snapshot['margin_rate']:.1%} on total sales of {money_local(snapshot['total_sales'])}."
    )

    if dims:
        for dim in dims:
            g = df.groupby(dim).agg(sales=("sales","sum"), margin=("margin","sum")).reset_index()
            g["margin_rate"] = safe_div(g["margin"].values, g["sales"].values)
            sales_cutoff = g["sales"].quantile(0.6)
            core = g[g["sales"] >= sales_cutoff].dropna(subset=["margin_rate"]).copy()
            if len(core) < 3:
                continue
            best = core.sort_values("margin_rate", ascending=False).iloc[0]
            worst = core.sort_values("margin_rate", ascending=True).iloc[0]
            insights.append(
                f"In {dim}, the strongest margin-rate contributor (among top sellers) is '{best[dim]}' "
                f"at {best['margin_rate']:.1%} on {money_local(best['sales'])} sales, while the weakest is "
                f"'{worst[dim]}' at {worst['margin_rate']:.1%} on {money_local(worst['sales'])} sales."
            )

    if yoy is not None and len(yoy) >= 2:
        last = yoy.iloc[-1]
        insights.append(
            f"Year-over-year, sales changed by {last['sales_yoy_pct']:.1%} and total margin changed by "
            f"{last['margin_yoy_pct']:.1%}. Margin rate shifted by {last['mr_change_bps']:.0f} bps vs prior year."
        )

    if anoms is not None and len(anoms) > 0:
        w = anoms.iloc[0]
        label_bits = []
        for key in ["division","category","brand","region"]:
            col = getattr(m, key, None)
            if col and col in anoms.columns and pd.notna(w.get(col, None)):
                label_bits.append(f"{key}={w[col]}")
        label = ", ".join(label_bits) if label_bits else "top anomaly"
        insights.append(
            f"Anomaly detection flagged extreme margin behavior: the most unusual record shows {label} "
            f"with margin rate {w['margin_rate']:.1%} on {money_local(w['sales'])} sales."
        )

    return insights[:10]