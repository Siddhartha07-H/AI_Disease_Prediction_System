
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

ROOT_DIR = Path(__file__).resolve().parent.parent

TRAIN_PATH = ROOT_DIR / "datasets" / "Training.csv"
TEST_PATH = ROOT_DIR / "datasets" / "Testing.csv"

train = pd.read_csv(TRAIN_PATH)
test = pd.read_csv(TEST_PATH)

# Remove unnecessary columns
train = train.loc[
    :, ~train.columns.astype(str).str.startswith("Unnamed")
]
test = test.loc[
    :, ~test.columns.astype(str).str.startswith("Unnamed")
]

# Check required target column
if "prognosis" not in train.columns or "prognosis" not in test.columns:
    raise ValueError("Both files must contain a prognosis column.")

X_train = train.drop(columns=["prognosis"])
y_train = train["prognosis"]

X_test = test.drop(columns=["prognosis"])
y_test = test["prognosis"]

# Align the test features to the training feature order
if set(X_train.columns) != set(X_test.columns):
    raise ValueError("Training and testing symptom columns do not match.")

X_test = X_test[X_train.columns]

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)
model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("Original Testing.csv evaluation")
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Accuracy:", round(accuracy * 100, 2), "%")
print("\nClassification report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)
print("\nExisting disease_model.pkl was not changed.")
print("This is not clinical validation.")
