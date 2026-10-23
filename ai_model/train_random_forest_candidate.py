
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_DIR / "datasets" / "Training.csv"
OUTPUT_PATH = PROJECT_DIR / "ai_model" / "random_forest_candidate.pkl"

# Load and clean the dataset.
data = pd.read_csv(DATA_PATH)
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]
data = data.drop_duplicates().reset_index(drop=True)

if "prognosis" not in data.columns:
    raise ValueError("The dataset must contain prognosis.")

X = data.drop(columns=["prognosis"])
y = data["prognosis"]

# Train a separate candidate model.
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1,
)

model.fit(X, y)

# Save the candidate separately.
joblib.dump(model, OUTPUT_PATH)

# Verify that the candidate can be loaded.
loaded_model = joblib.load(OUTPUT_PATH)

print("Random Forest candidate created successfully.")
print("Training rows:", len(X))
print("Disease classes:", y.nunique())
print("Input features:", X.shape[1])
print("Candidate file:", OUTPUT_PATH)
print("Reload test:", type(loaded_model).__name__)
print("\nThe existing disease_model.pkl was not changed.")
print("This candidate is not clinically validated.")
