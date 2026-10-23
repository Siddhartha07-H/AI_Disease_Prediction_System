
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "datasets" / "Training.csv"


def main():
    df = pd.read_csv(DATA_PATH)

    # Remove unused columns.
    df = df.loc[
        :, ~df.columns.astype(str).str.startswith("Unnamed")
    ]

    print("Total rows:", len(df))
    print("Total columns:", len(df.columns))
    print("Exact duplicate rows:", int(df.duplicated().sum()))

    # Check how many unique symptom patterns exist.
    features = df.drop(columns=["prognosis"])
    labels = df["prognosis"]

    unique_patterns = features.drop_duplicates()

    print("Unique symptom patterns:", len(unique_patterns))
    print("\nDisease counts:")
    print(labels.value_counts().sort_index().to_string())

    # Count how many different diseases share the same symptom pattern.
    pattern_data = features.copy()
    pattern_data["prognosis"] = labels

    disease_counts_per_pattern = (
        pattern_data.groupby(list(features.columns), dropna=False)["prognosis"]
        .nunique()
    )

    ambiguous_patterns = disease_counts_per_pattern[
        disease_counts_per_pattern > 1
    ]

    print(
        "\nSymptom patterns associated with multiple diseases:",
        len(ambiguous_patterns),
    )

    print("\nCheck complete. No files were modified.")


if __name__ == "__main__":
    main()
