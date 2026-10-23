
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

# Find the main project folder.
ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT_DIR / "datasets" / "Training.csv"

# Check that the dataset exists.
if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Training dataset not found: {DATASET_PATH}"
    )

# Load the dataset.
data = pd.read_csv(DATASET_PATH)

# Remove unwanted unnamed columns.
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]

if "prognosis" not in data.columns:
    raise ValueError("The dataset must contain prognosis.")

# Remove duplicate rows so repeated examples do not
# inflate the evaluation score.
data = data.drop_duplicates().reset_index(drop=True)

print("Unique dataset shape:", data.shape)
print("Number of diseases:", data["prognosis"].nunique())

# Separate symptoms (X) and disease labels (y).
X = data.drop(columns=["prognosis"])
y = data["prognosis"]

# Split the unique rows into training and test sets.
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y,
)

# Train a separate evaluation model.
# This does not overwrite disease_model.pkl.
model = DecisionTreeClassifier(random_state=42)
model.fit(X_train, y_train)

# Evaluate on the held-out rows.
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nEvaluation completed.")
print(f"Accuracy: {accuracy * 100:.2f}%")

print("\nClassification report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0,
    )
)

# Save the confusion matrix as a CSV file.
labels = sorted(y.unique())

matrix = confusion_matrix(
    y_test,
    predictions,
    labels=labels,
)

matrix_path = ROOT_DIR / "ai_model" / "confusion_matrix.csv"

pd.DataFrame(
    matrix,
    index=labels,
    columns=labels,
).to_csv(matrix_path)

print("\nConfusion matrix saved to:")
print(matrix_path)

print("\nThe existing saved model was not changed.")
