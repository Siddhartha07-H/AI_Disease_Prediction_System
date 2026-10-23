
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score

ROOT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = ROOT_DIR / "ai_model" / "disease_model.pkl"
TEST_PATH = ROOT_DIR / "datasets" / "Testing.csv"

# Load the existing saved model
model = joblib.load(MODEL_PATH)

test = pd.read_csv(TEST_PATH)
test = test.loc[
    :, ~test.columns.astype(str).str.startswith("Unnamed")
]

X_test = test.drop(columns=["prognosis"])
y_test = test["prognosis"]

# Ensure the test features match the model's expected features
if hasattr(model, "feature_names_in_"):
    expected_features = list(model.feature_names_in_)

    if set(expected_features) != set(X_test.columns):
        raise ValueError("Saved model features do not match Testing.csv.")

    X_test = X_test[expected_features]

predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print("Saved model inspection")
print("Model type:", type(model).__name__)
print("Test samples:", len(X_test))
print("Accuracy on Testing.csv:", round(accuracy * 100, 2), "%")

if hasattr(model, "n_features_in_"):
    print("Expected input features:", model.n_features_in_)

print("\nThe saved model was only inspected, not changed.")
print("This result is not clinical validation.")
