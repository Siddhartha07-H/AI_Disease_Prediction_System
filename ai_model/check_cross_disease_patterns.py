
from pathlib import Path
from collections import defaultdict

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "datasets" / "Training.csv"

data = pd.read_csv(DATA_PATH)
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]
data = data.drop_duplicates().reset_index(drop=True)

X = data.drop(columns=["prognosis"])
y = data["prognosis"]

# Group symptom patterns by their exact binary values.
pattern_labels = defaultdict(set)

for row, label in zip(X.to_numpy(), y):
    pattern_labels[tuple(row)].add(label)

# Find exact symptom patterns associated with multiple diseases.
conflicts = []

for pattern, labels in pattern_labels.items():
    if len(labels) > 1:
        conflicts.append(sorted(labels))

print("Unique symptom patterns:", len(pattern_labels))
print("Patterns linked to multiple disease labels:", len(conflicts))

if conflicts:
    print("\nConflicting labels:")
    for labels in conflicts[:20]:
        print(labels)
else:
    print("No exact pattern has multiple disease labels.")

# Compare the number of symptoms in each pattern.
symptom_counts = X.sum(axis=1)

print("\nSymptoms per pattern:")
print(symptom_counts.describe().to_string())

print("\nExisting saved model was not changed.")
