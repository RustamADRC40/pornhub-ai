"""Offline CLI demo for phishing URL screening."""

import argparse
from pathlib import Path

import joblib

from .features import extract_url_features


def demo(url: str) -> dict:
    model_path = Path("models/random_forest.joblib")
    if not model_path.exists():
        return {
            "url": url,
            "status": "model_not_trained",
            "features": extract_url_features(url),
        }

    model = joblib.load(model_path)
    features = extract_url_features(url)
    import pandas as pd

    frame = pd.DataFrame([features])
    prediction = model.predict(frame)[0]
    probability = model.predict_proba(frame)[0].tolist()

    return {
        "url": url,
        "prediction": str(prediction),
        "probability_by_class": dict(zip(model.classes_.tolist(), probability)),
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen a URL using only lexical features")
    parser.add_argument("url")
    args = parser.parse_args()
    print(demo(args.url))


if __name__ == "__main__":
    main()
