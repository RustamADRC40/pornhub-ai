"""Training entry point for reproducible phishing URL experiments."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42


def train_models(csv_path: str, target_column: str = "label") -> dict:
    frame = pd.read_csv(csv_path)
    if target_column not in frame.columns:
        raise ValueError(f"Missing target column: {target_column}")

    X = frame.drop(columns=[target_column])
    y = frame[target_column]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )

    numeric_columns = X.select_dtypes(include="number").columns.tolist()
    categorical_columns = X.select_dtypes(exclude="number").columns.tolist()

    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    preprocessing = ColumnTransformer([
        ("numeric", numeric, numeric_columns),
        ("categorical", "passthrough", categorical_columns),
    ], remainder="drop")

    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "random_forest": RandomForestClassifier(n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1),
    }

    results = {}
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    for name, classifier in models.items():
        pipeline = Pipeline([
            ("preprocessing", preprocessing),
            ("classifier", classifier),
        ])
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

        results[name] = {
            "accuracy": accuracy_score(y_test, predictions),
            "classification_report": classification_report(y_test, predictions, output_dict=True),
            "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        }
        joblib.dump(pipeline, models_dir / f"{name}.joblib")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--target", default="label")
    args = parser.parse_args()
    print(train_models(args.csv_path, args.target))
