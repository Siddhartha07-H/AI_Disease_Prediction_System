
from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

data = pd.read_csv(ROOT / "datasets" / "Training.csv")
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]
data = data.drop_duplicates().reset_index(drop=True)

X = data.drop(columns=["prognosis"])

old_model = joblib.load(ROOT / "ai_model" / "disease_model.pkl")
new_model = joblib.load(
    ROOT / "ai_model" / "random_forest_candidate.pkl"
)

old_predictions = old_model.predict(X)
new_predictions = new_model.predict(X)

agreement = (old_predictions == new_predictions).mean() * 100

print("Dataset rows tested:", len(X))
print("Existing model:", type(old_model).__name__)
print("Candidate model:", type(new_model).__name__)
print(f"Prediction agreement: {agreement:.2f}%")
print("Different predictions:", (old_predictions != new_predictions).sum())
print("\nExisting model remains unchanged.")
