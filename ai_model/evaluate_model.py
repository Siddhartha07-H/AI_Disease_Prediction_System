
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

# Project folder
ROOT = Path(__file__).resolve().parent.parent

TRAIN_PATH = ROOT / "datasets" / "Training.csv"
TEST_PATH = ROOT / "datasets" / "Testing.csv"
MODEL_PATH = ROOT / "ai_model" / "disease_model.pkl"


def clean_dataset(path):
    df = pd.read_csv(path)

    # Remove unnecessary columns
    df = df.loc[
        :, ~df.columns.astype(str).str.startswith("Unnamed")
    ]

    if "prognosis" not in df.columns:
        raise ValueError(f"'prognosis' column missing in {path.name}")

    return df


def main():
    print("Loading datasets and saved model...")

    train = clean_dataset(TRAIN_PATH)
    test = clean_dataset(TEST_PATH)
    model = joblib.load(MODEL_PATH)

    X_train = train.drop(columns=["prognosis"])
    y_test = test["prognosis"]

    # Use the feature names expected by the saved model
    expected_features = list(
        getattr(model, "feature_names_in_", X_train.columns)
    )

    missing_in_test = [
        col for col in expected_features if col not in test.columns
    ]

    extra_in_test = [
        col for col in test.columns
        if col not in expected_features and col != "prognosis"
    ]

    print("\nTraining rows:", len(train))
    print("Testing rows:", len(test))
    print("Model features:", len(expected_features))
    print("Training diseases:", train["prognosis"].nunique())
    print("Testing diseases:", y_test.nunique())

    if missing_in_test:
        print("\nMissing test features:", missing_in_test)
        raise ValueError("Test dataset does not match model features.")

    if extra_in_test:
        print("\nExtra test features:", extra_in_test)

    X_test = test[expected_features]

    if list(X_test.columns) != expected_features:
        raise ValueError("Feature order does not match the model.")

    print("\nEvaluating the saved model...")
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print(f"\nTest accuracy: {accuracy * 100:.2f}%")

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print("\nConfusion matrix:")
    print(confusion_matrix(y_test, predictions))

    # Check the one-symptom behavior without changing the model
    print("\nOne-symptom software checks:")

    for symptom in ["itching", "cough", "joint_pain"]:
        if symptom not in expected_features:
            print(f"{symptom}: not a model feature")
            continue

        sample = pd.DataFrame(
            [[0] * len(expected_features)],
            columns=expected_features
        )
        sample.loc[0, symptom] = 1

        result = model.predict(sample)[0]
        print(f"{symptom} -> {result}")

    print("\nEvaluation complete. The saved model was not changed.")


if __name__ == "__main__":
    main()
