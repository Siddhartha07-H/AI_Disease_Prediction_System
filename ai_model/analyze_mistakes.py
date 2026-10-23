
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "datasets" / "Training.csv"

# Load the dataset
data = pd.read_csv(DATA_PATH)

# Remove unnecessary columns
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]

# Remove duplicate rows for a more informative evaluation
data = data.drop_duplicates().reset_index(drop=True)

X = data.drop(columns=["prognosis"])
y = data["prognosis"]

# Use the same split settings as your evaluation script
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

# Train a separate evaluation model.
# This does NOT overwrite disease_model.pkl.
model = DecisionTreeClassifier(random_state=42)
model.fit(X_train, y_train)

predictions = model.predict(X_test)

# Save only the incorrect predictions for inspection
mistakes = pd.DataFrame({
    "Actual disease": y_test.to_numpy(),
    "Predicted disease": predictions
})

mistakes = mistakes[
    mistakes["Actual disease"] != mistakes["Predicted disease"]
]

output_path = ROOT_DIR / "ai_model" / "model_mistakes.csv"
mistakes.to_csv(output_path, index=False)

print("Mistake analysis completed.")
print("Incorrect predictions:", len(mistakes))
print("Saved file:", output_path)

if mistakes.empty:
    print("No mistakes found in this evaluation split.")
else:
    print("\nMost common confusion pairs:")
    print(
        mistakes.groupby(
            ["Actual disease", "Predicted disease"]
        ).size().sort_values(ascending=False).head(15)
    )

print("\nThe existing saved model was not changed.")
