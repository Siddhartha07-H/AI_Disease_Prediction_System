
from pathlib import Path

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "datasets" / "Training.csv"
MODEL_PATH = ROOT / "ai_model" / "disease_model_candidate.pkl"

def main():
    data = pd.read_csv(DATA_PATH)
    data = data.loc[
        :, ~data.columns.astype(str).str.startswith("Unnamed")
    ]

    # Remove repeated complete records.
    data = data.drop_duplicates().reset_index(drop=True)

    X = data.drop(columns=["prognosis"])
    y = data["prognosis"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print("Unique records:", len(data))
    print("Training records:", len(X_train))
    print("Test records:", len(X_test))
    print("Candidate accuracy:",
          round(accuracy_score(y_test, predictions) * 100, 2), "%")
    print("\nClassification report:")
    print(classification_report(
        y_test, predictions, zero_division=0
    ))

    # Save separately; do not replace the existing model.
    joblib.dump(model, MODEL_PATH)
    print("\nCandidate model saved to:", MODEL_PATH)
    print("Existing disease_model.pkl was not changed.")

if __name__ == "__main__":
    main()
