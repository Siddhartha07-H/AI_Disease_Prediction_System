
from pathlib import Path
import joblib
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_DIR / "ai_model" / "random_forest_candidate.pkl"
DATA_PATH = PROJECT_DIR / "datasets" / "Training.csv"

# Load the saved model and dataset
model = joblib.load(MODEL_PATH)

data = pd.read_csv(DATA_PATH)
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]
data = data.drop_duplicates().reset_index(drop=True)

X = data.drop(columns=["prognosis"])
y = data["prognosis"]

# Select one existing dataset example
sample = X.iloc[[0]]
actual_disease = y.iloc[0]

# Make a prediction
predicted_disease = model.predict(sample)[0]

print("Model:", type(model).__name__)
print("Actual disease:", actual_disease)
print("Predicted disease:", predicted_disease)
print("Prediction matches:", actual_disease == predicted_disease)
print("Input features:", sample.shape[1])
