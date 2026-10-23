
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "datasets" / "Training.csv"

data = pd.read_csv(DATA_PATH)

# Remove unnecessary columns and exact duplicate rows
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]
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

# Convert each symptom pattern into a comparable tuple
train_patterns = {
    tuple(row)
    for row in X_train.to_numpy()
}

test_patterns = [
    tuple(row)
    for row in X_test.to_numpy()
]

overlap = sum(
    pattern in train_patterns
    for pattern in test_patterns
)

print("Unique dataset rows:", len(data))
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Overlapping symptom patterns:", overlap)
print(
    "Overlap percentage:",
    round(overlap / len(test_patterns) * 100, 2),
    "%"
)
print("\nExisting saved model was not changed.")
