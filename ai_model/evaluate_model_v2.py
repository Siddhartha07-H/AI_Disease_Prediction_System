
from pathlib import Path

import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "datasets" / "Training.csv"


def main():
    data = pd.read_csv(DATA_PATH)

    # Remove unnecessary columns.
    data = data.loc[
        :, ~data.columns.astype(str).str.startswith("Unnamed")
    ]

    if "prognosis" not in data.columns:
        raise ValueError("The prognosis column is missing.")

    # Check for exact duplicate rows.
    duplicate_count = int(data.duplicated().sum())

    print("Dataset rows:", len(data))
    print("Disease classes:", data["prognosis"].nunique())
    print("Exact duplicate rows:", duplicate_count)

    X = data.drop(columns=["prognosis"])
    y = data["prognosis"]

    # Keep examples from every disease in both sets.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    # Use the same model type and settings as the original script.
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print("\nStratified holdout evaluation")
    print("Training examples:", len(X_train))
    print("Holdout examples:", len(X_test))
    print(f"Accuracy: {accuracy * 100:.2f}%")

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    # Display only incorrect predictions.
    results = pd.DataFrame({
        "actual": y_test,
        "predicted": predictions,
    })

    errors = results[results["actual"] != results["predicted"]]

    print("\nIncorrect predictions:", len(errors))

    if errors.empty:
        print("No incorrect predictions in this holdout set.")
    else:
        print(errors.to_string())

    print("\nConfusion matrix shape:")
    print(confusion_matrix(y_test, predictions).shape)

    print(
        "\nEvaluation finished. "
        "The saved disease_model.pkl was not changed."
    )


if __name__ == "__main__":
    main()
