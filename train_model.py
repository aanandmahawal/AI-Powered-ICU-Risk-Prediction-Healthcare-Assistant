"""
train_model.py - trains the RiskCare ICU risk model.

    python train_model.py
    python train_model.py --data path/to/file.csv

Data
----
data/RiskCare_ICU_Dataset_26000_patients.csv (see data/README.md): 26,000 synthetic adult
patients, one row per patient, 10 clinical parameters and a 0/1 `icu_admission` outcome.

Training
--------
- stratified 70 / 15 / 15 split into training, validation and test patients
- XGBoost with early stopping on the validation set
- monotone constraints so risk only rises with age, comorbidity, supplemental oxygen and
  reduced consciousness, and only falls as SpO2 improves
- 5-fold stratified cross-validation for the headline ROC-AUC

Outputs
-------
model/icu_xgb_model.json   XGBoost model (portable JSON format)
model/model_meta.json      dataset summary, parameters and evaluation metrics used by the app
"""

import argparse
import json
import os
from datetime import date

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from xgboost import XGBClassifier

from clinical import FEATURES, FEATURE_KEYS, news2_score

SEED = 42
DEFAULT_DATA = os.path.join("data", "RiskCare_ICU_Dataset_26000_patients.csv")
MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "icu_xgb_model.json")
META_PATH = os.path.join(MODEL_DIR, "model_meta.json")

COLUMN_MAP = {
    "age_years": "Age",
    "heart_rate_bpm": "HR",
    "systolic_bp_mmhg": "SBP",
    "diastolic_bp_mmhg": "DBP",
    "respiratory_rate_bpm": "RespRate",
    "spo2_percent": "SpO2",
    "temperature_f": "Temp",
    "supplemental_oxygen": "SuppO2",
    "level_of_consciousness": "Consciousness",
    "comorbidity_index": "ComorbidityIndex",
    "icu_admission": "ICU",
}

# ACVPU text -> ordinal used by the model (0 = Alert ... 4 = Unresponsive)
CONSCIOUSNESS_CODES = {
    "alert": 0, "confusion": 1, "new confusion": 1,
    "voice": 2, "pain": 3, "unresponsive": 4,
}

# Clinical direction of each feature: +1 risk only rises, -1 risk only falls, 0 unconstrained.
MONOTONE = {
    "Age": 1, "HR": 0, "SBP": 0, "DBP": 0, "RespRate": 0, "SpO2": -1,
    "Temp": 0, "SuppO2": 1, "Consciousness": 1, "ComorbidityIndex": 1,
}

PARAMS = dict(
    n_estimators=2000,
    learning_rate=0.02,
    max_depth=3,
    min_child_weight=10,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=2.0,
    objective="binary:logistic",
    eval_metric="logloss",
    tree_method="hist",
    monotone_constraints=tuple(MONOTONE[k] for k in FEATURE_KEYS),
    random_state=SEED,
)


def load(path):
    raw = pd.read_csv(path)
    missing = [c for c in COLUMN_MAP if c not in raw.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    df = raw[list(COLUMN_MAP)].rename(columns=COLUMN_MAP)
    df["Consciousness"] = df["Consciousness"].astype(str).str.strip().str.lower().map(CONSCIOUSNESS_CODES)

    ok = df.notna().all(axis=1) & df["ICU"].isin([0, 1]) & (df["DBP"] < df["SBP"])
    for f in FEATURES:
        ok &= df[f["key"]].between(f["min"], f["max"])
    if not ok.all():
        print(f"Skipping {int((~ok).sum())} invalid rows")
    df = df[ok].astype({k: int for k in FEATURE_KEYS + ["ICU"] if k != "Temp"})

    source = raw.loc[df.index, "source"] if "source" in raw.columns else pd.Series("cohort", index=df.index)
    return df.reset_index(drop=True), source.reset_index(drop=True)


def calibration_table(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    rows = []
    for b in range(bins):
        m = idx == b
        if m.sum() >= 20:
            rows.append({"bin": f"{edges[b]:.1f}-{edges[b + 1]:.1f}", "n": int(m.sum()),
                         "mean_predicted": round(float(p[m].mean()), 3),
                         "observed_rate": round(float(y[m].mean()), 3)})
    return rows


def fit(X_train, y_train, X_val, y_val):
    clf = XGBClassifier(**PARAMS, early_stopping_rounds=150)
    clf.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return clf


def cross_validate(X, y, strata, folds=5):
    aucs = []
    for tr, te in StratifiedKFold(folds, shuffle=True, random_state=SEED).split(X, strata):
        X_tr, X_va, y_tr, y_va = train_test_split(
            X.iloc[tr], y.iloc[tr], test_size=0.15, stratify=strata.iloc[tr], random_state=SEED)
        clf = fit(X_tr, y_tr, X_va, y_va)
        aucs.append(roc_auc_score(y.iloc[te], clf.predict_proba(X.iloc[te])[:, 1]))
    return float(np.mean(aucs)), float(np.std(aucs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DEFAULT_DATA)
    args = ap.parse_args()

    df, source = load(args.data)
    X, y = df[FEATURE_KEYS], df["ICU"]
    strata = source + "_" + y.astype(str)          # keep the dataset's composition in every split
    print(f"Patients: {len(df):,} | ICU admissions: {y.mean():.1%}")

    cv_mean, cv_std = cross_validate(X, y, strata)
    print(f"5-fold CV ROC-AUC {cv_mean:.3f} +/- {cv_std:.3f}")

    X_tmp, X_test, y_tmp, y_test, s_tmp, s_test = train_test_split(
        X, y, strata, test_size=0.15, stratify=strata, random_state=SEED)
    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp, test_size=0.15 / 0.85, stratify=s_tmp, random_state=SEED)

    clf = fit(X_train, y_train, X_val, y_val)
    p_test = clf.predict_proba(X_test)[:, 1]
    news2_test = np.array([news2_score(r)[0] for r in X_test.to_dict("records")])
    cohort = s_test.str.startswith("cohort").to_numpy()

    metrics = {
        "cv_roc_auc_mean": round(cv_mean, 4),
        "cv_roc_auc_std": round(cv_std, 4),
        "roc_auc": round(float(roc_auc_score(y_test, p_test)), 4),
        "roc_auc_core_cohort": round(float(roc_auc_score(y_test[cohort], p_test[cohort])), 4),
        "brier": round(float(brier_score_loss(y_test, p_test)), 4),
        "log_loss": round(float(log_loss(y_test, p_test)), 4),
        "news2_roc_auc": round(float(roc_auc_score(y_test, news2_test)), 4),
    }

    os.makedirs(MODEL_DIR, exist_ok=True)
    clf.save_model(MODEL_PATH)

    meta = {
        "model": "XGBoost gradient-boosted trees (binary:logistic)",
        "trained_on": str(date.today()),
        "dataset": os.path.basename(args.data),
        "n_patients": int(len(df)),
        "icu_prevalence": round(float(y.mean()), 4),
        "n_train": int(len(X_train)), "n_val": int(len(X_val)), "n_test": int(len(X_test)),
        "features": FEATURE_KEYS,
        "monotone_constraints": MONOTONE,
        "n_trees": int(clf.best_iteration + 1),
        "params": {k: PARAMS[k] for k in ["learning_rate", "max_depth", "min_child_weight",
                                           "subsample", "colsample_bytree", "reg_lambda"]},
        "test_metrics": metrics,
        "calibration": calibration_table(y_test.to_numpy(), p_test),
    }
    with open(META_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"Trees: {meta['n_trees']}")
    print("Test metrics:", json.dumps(metrics, indent=2))
    print("Calibration (predicted vs observed):")
    for r in meta["calibration"]:
        print(f"  {r['bin']}: n={r['n']:>5}  predicted {r['mean_predicted']:.3f}  observed {r['observed_rate']:.3f}")
    print(f"Saved {MODEL_PATH} and {META_PATH}")


if __name__ == "__main__":
    main()
