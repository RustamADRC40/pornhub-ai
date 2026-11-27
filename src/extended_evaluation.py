"""URL-only audit, permutation feature importance and safe adversarial checks."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
URL_COLUMNS = [
    "URLLength", "DomainLength", "IsDomainIP", "TLDLength", "NoOfSubDomain",
    "NoOfLettersInURL", "LetterRatioInURL", "NoOfDegitsInURL", "DegitRatioInURL",
    "NoOfEqualsInURL", "NoOfQMarkInURL", "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL", "SpacialCharRatioInURL", "IsHTTPS",
]


def url_only_evaluation(csv_path: str) -> dict:
    frame = pd.read_csv(csv_path)
    available = [column for column in URL_COLUMNS if column in frame.columns]
    X = frame[available].fillna(frame[available].median(numeric_only=True))
    y = frame["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    result = {
        "features_used": available,
        "test_instances": int(len(X_test)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision_phishing": float(precision_score(y_test, pred, pos_label=0, zero_division=0)),
        "recall_phishing": float(recall_score(y_test, pred, pos_label=0, zero_division=0)),
        "f1_phishing": float(f1_score(y_test, pred, pos_label=0, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, pred, labels=[0, 1]).tolist(),
        "random_seed": RANDOM_STATE,
    }

    importance = permutation_importance(
        model, X_test, y_test, scoring="f1", n_repeats=10,
        random_state=RANDOM_STATE, n_jobs=-1
    )
    result["permutation_importance"] = {
        column: {
            "mean": float(mean),
            "std": float(std),
        }
        for column, mean, std in zip(
            available,
            importance.importances_mean,
            importance.importances_std,
        )
    }

    output = Path("reports")
    output.mkdir(exist_ok=True)
    (output / "url_only_audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    joblib.dump(model, Path("models") / "phiusiil_url_only_random_forest.joblib")
    return result


def safe_adversarial_examples() -> pd.DataFrame:
    """Generate synthetic feature mutations; no network or real-domain contact."""
    base = {
        "URLLength": 23,
        "DomainLength": 16,
        "IsDomainIP": 0,
        "TLDLength": 2,
        "NoOfSubDomain": 1,
        "NoOfLettersInURL": 9,
        "LetterRatioInURL": 0.391,
        "NoOfDegitsInURL": 0,
        "DegitRatioInURL": 0.0,
        "NoOfEqualsInURL": 0,
        "NoOfQMarkInURL": 0,
        "NoOfAmpersandInURL": 0,
        "NoOfOtherSpecialCharsInURL": 2,
        "SpacialCharRatioInURL": 0.087,
        "IsHTTPS": 1,
    }
    variants = {}
    variants["base"] = base.copy()
    variants["add_subdomain"] = {**base, "URLLength": 36, "NoOfSubDomain": 4, "DomainLength": 29}
    variants["ip_host"] = {**base, "IsDomainIP": 1, "URLLength": 31}
    variants["remove_https"] = {**base, "IsHTTPS": 0}
    variants["many_parameters"] = {**base, "NoOfEqualsInURL": 8, "NoOfQMarkInURL": 3,
                                  "URLLength": 48, "DegitRatioInURL": 0.25}

    frame = pd.DataFrame(variants).T
    frame.index.name = "synthetic_variant"
    return frame.reset_index()


if __name__ == "__main__":
    result = url_only_evaluation("data/raw/PhiUSIIL_Phishing_URL_Dataset.csv")
    variants = safe_adversarial_examples()
    variants.to_csv("reports/synthetic_adversarial_examples.csv", index=False)

    model = joblib.load("models/phiusiil_url_only_random_forest.joblib")
    predictions = model.predict(variants.drop(columns=["synthetic_variant"]))
    probabilities = model.predict_proba(variants.drop(columns=["synthetic_variant"]))[:, 1]
    variants["predicted_label"] = predictions
    variants["legitimate_probability"] = probabilities
    variants.to_csv("reports/synthetic_adversarial_results.csv", index=False)

    print(json.dumps(result, ensure_ascii=False, indent=2))
