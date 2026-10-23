
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
)

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_DIR / "datasets" / "Training.csv"

print("=" * 60)
print("RANDOM FOREST: UNIQUE-PATTERN EVALUATION")
print("=" * 60)

# Load dataset
data = pd.read_csv(DATASET_PATH)

# Remove unwanted unnamed columns
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]

# Remove exact duplicate rows
data = data.drop_duplicates().reset_index(drop=True)

# Separate symptoms and target labels
X = data.drop(columns=["prognosis"])
y = data["prognosis"]

print("Unique rows:", len(data))
print("Number of diseases:", y.nunique())

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y,
)

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))

# Train a new experiment model (does not replace saved model)
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1,
)

model.fit(X_train, y_train)

# Evaluate predictions
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
macro_f1 = f1_score(
    y_test,
    predictions,
    average="macro",
    zero_division=0,
)

print("\nEvaluation results")
print("Accuracy:", round(accuracy * 100, 2), "%")
print("Macro F1:", round(macro_f1, 3))

print("\nClassification report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0,
    )
)

# Save incorrect predictions for review
mistakes = pd.DataFrame({
    "Actual disease": y_test.to_numpy(),
    "Predicted disease": predictions,
})

mistakes = mistakes[
    mistakes["Actual disease"] != mistakes["Predicted disease"]
]

output_path = PROJECT_DIR / "ai_model" / "random_forest_unique_mistakes.csv"
mistakes.to_csv(output_path, index=False)

print("\nIncorrect predictions:", len(mistakes))
print("Mistakes saved to:", output_path)
print("\nExisting disease_model.pkl was not changed.")
print("This experiment is not clinical validation.")
