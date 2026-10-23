
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = ROOT / "datasets" / "Training.csv"
MODEL_PATH = ROOT / "ai_model" / "disease_model.pkl"


def main():
    data = pd.read_csv(DATA_PATH)

    data = data.loc[
        :, ~data.columns.astype(str).str.startswith("Unnamed")
    ]

    X = data.drop(columns=["prognosis"])
    y = data["prognosis"]

    model = joblib.load(MODEL_PATH)

    features = list(model.feature_names_in_)

    print("Checking single-symptom model behavior")
    print("This script does not change the saved model.\n")

    for symptom in ["itching", "cough", "joint_pain"]:
        if symptom not in features:
            print(f"{symptom}: feature not found")
            continue

        sample = pd.DataFrame(
            0,
            index=[0],
            columns=features,
        )
        sample.loc[0, symptom] = 1

        prediction = model.predict(sample)[0]

        matching_rows = data[X[symptom] == 1]
        diseases = sorted(matching_rows["prognosis"].unique())

        print(f"Symptom: {symptom}")
        print(f"Model prediction: {prediction}")
        print(f"Diseases containing this symptom in the dataset: {diseases}")
        print(f"Matching training rows: {len(matching_rows)}")
        print("-" * 60)


if __name__ == "__main__":
    main()
