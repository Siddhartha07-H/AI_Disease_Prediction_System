
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "datasets" / "Training.csv"

def main():
    data = pd.read_csv(DATA_PATH)
    data = data.loc[
        :, ~data.columns.astype(str).str.startswith("Unnamed")
    ]

    symptoms = data.drop(columns=["prognosis"])
    labels = data["prognosis"]

    test_cases = [
        ["itching", "skin_rash"],
        ["cough", "high_fever"],
        ["joint_pain", "muscle_pain"],
        ["itching", "skin_rash", "nodal_skin_eruptions"],
    ]

    print("Checking symptom patterns in the training dataset\n")

    for selected in test_cases:
        unknown = [s for s in selected if s not in symptoms.columns]

        print("Selected symptoms:", ", ".join(selected))

        if unknown:
            print("Unknown symptoms:", unknown)
            print("-" * 55)
            continue

        sample = pd.Series(0, index=symptoms.columns, dtype=int)
        sample.loc[selected] = 1

        # Find exact matches across all symptom columns.
        distances = symptoms.ne(sample, axis="columns").sum(axis=1)
        exact_matches = distances == 0

        if exact_matches.any():
            print("Exact matching rows:", int(exact_matches.sum()))
            print("Matching disease labels:")
            print(labels[exact_matches].value_counts().to_string())
        else:
            print("Exact matching rows: 0")

            # Find the closest patterns in the dataset.
            minimum_distance = int(distances.min())
            nearest = distances == minimum_distance

            print("Minimum differing symptoms:", minimum_distance)
            print("Closest matching disease labels:")
            print(labels[nearest].value_counts().head(10).to_string())

        print("-" * 55)

if __name__ == "__main__":
    main()
