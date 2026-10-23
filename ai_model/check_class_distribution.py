
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "datasets" / "Training.csv"

data = pd.read_csv(DATA_PATH)

# Remove unnecessary columns and duplicate rows
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]
data = data.drop_duplicates().reset_index(drop=True)

counts = data["prognosis"].value_counts().sort_values()

print("Number of unique rows:", len(data))
print("Number of diseases:", data["prognosis"].nunique())

print("\nUnique symptom patterns per disease:")
print(counts.to_string())

print("\nDiseases with fewer than 5 unique patterns:")
print(counts[counts < 5].to_string())

output_path = ROOT_DIR / "ai_model" / "class_distribution.csv"
counts.rename_axis("Disease").reset_index(
    name="Unique patterns"
).to_csv(output_path, index=False)

print(f"\nSaved distribution to: {output_path}")
print("The existing saved model was not changed.")
