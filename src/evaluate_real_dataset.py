"""Reproducible training and evaluation on the PhiUSIIL real dataset."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
RAW_COLUMNS_TO_DROP = [
    "FILENAME", "URL", "Domain", "TLD", "Title",
]


def prepare_data(csv_path: str):
    frame = pd.read_csv(csv_path)
    if "label" not in frame.columns:
        raise ValueError("Column 'label' is required")

    frame = frame.drop_duplicates()
    y = frame["label"]
    X = frame.drop(columns=["label"] + [c for c in RAW_COLUMNS_TO_DROP if c in frame.columns])

    # Keep only numeric model features. Raw URL/domain/title text is excluded.
    X = X.select_dtypes(include=[np.number])
    if X.isna().sum().sum():
        X = X.fillna(X.median(numeric_only=True))

    return X, y


def evaluate_real_dataset(csv_path: str, seed: int = RANDOM_STATE) -> dict:
    X, y = prepare_data(csv_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=seed, stratify=y
    )

    scaler = ColumnTransformer(
        [("scale", StandardScaler(), X.columns.tolist())],
        remainder="drop",
    )

    classifiers = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=seed, n_jobs=-1
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1,
        ),
        "mlp": MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            max_iter=100,
            early_stopping=True,
            random_state=seed,
        ),
    }

    results = {}
    output_dir = Path("reports")
    model_dir = Path("models")
    output_dir.mkdir(exist_ok=True)
    model_dir.mkdir(exist_ok=True)

    for name, classifier in classifiers.items():
        pipeline = Pipeline([
            ("scaler", scaler),
            ("classifier", classifier),
        ])
        pipeline.fit(X_train, y_train)

        pred = pipeline.predict(X_test)
        positive_scores = pipeline.predict_proba(X_test)[:, 1]
        cm = confusion_matrix(y_test, pred, labels=[0, 1])

        results[name] = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "precision": float(precision_score(y_test, pred, pos_label=0, zero_division=0)),
            "recall": float(recall_score(y_test, pred, pos_label=0, zero_division=0)),
            "f1": float(f1_score(y_test, pred, pos_label=0, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, positive_scores)),
            "average_precision": float(average_precision_score(y_test, positive_scores)),
            "confusion_matrix_labels_0_1": cm.tolist(),
        }

        joblib.dump(pipeline, model_dir / f"phiusiil_{name}.joblib")

    metadata = {
        "dataset": "PhiUSIIL Phishing URL (Website)",
        "source": "https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+website",
        "license": "CC BY 4.0",
        "instances_after_deduplication": int(len(X)),
        "features_used": int(X.shape[1]),
        "train_instances": int(len(X_train)),
        "test_instances": int(len(X_test)),
        "class_counts": y.value_counts().sort_index().to_dict(),
        "random_seed": seed,
        "test_fraction": 0.20,
        "label_meaning": {"0": "phishing", "1": "legitimate"},
        "raw_columns_removed": RAW_COLUMNS_TO_DROP,
        "models": results,
    }

    (output_dir / "phiusiil_metrics.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame(results).T.to_csv(output_dir / "model_metrics.csv")

    return metadata


if __name__ == "__main__":
    print(json.dumps(evaluate_real_dataset("data/raw/PhiUSIIL_Phishing_URL_Dataset.csv"), ensure_ascii=False, indent=2))
