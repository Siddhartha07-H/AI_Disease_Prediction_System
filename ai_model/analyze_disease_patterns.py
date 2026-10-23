
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_DIR / "datasets" / "Training.csv"

data = pd.read_csv(DATASET_PATH)

# Remove unwanted unnamed columns
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]

# Remove duplicate rows
data = data.drop_duplicates().reset_index(drop=True)

# Count the distinct symptom patterns for each disease
pattern_counts = (
    data.groupby("prognosis")
    .size()
    .sort_values()
    .rename("unique_patterns")
    .reset_index()
)

print("=" * 55)
print("DISEASE SYMPTOM PATTERN ANALYSIS")
print("=" * 55)

print("Unique dataset rows:", len(data))
print("Number of diseases:", data["prognosis"].nunique())

print("\nDiseases with the fewest patterns:")
print(pattern_counts.head(15).to_string(index=False))

print("\nDiseases with the most patterns:")
print(pattern_counts.tail(15).to_string(index=False))

print("\nPattern count summary:")
print(pattern_counts["unique_patterns"].describe())

output_path = PROJECT_DIR / "ai_model" / "disease_pattern_analysis.csv"
pattern_counts.to_csv(output_path, index=False)

print("\nReport saved to:", output_path)
print("The saved prediction model was not changed.")
print("This analysis is not clinical validation.")
