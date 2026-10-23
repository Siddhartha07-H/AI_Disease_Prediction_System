
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_DIR / "datasets" / "Training.csv"

data = pd.read_csv(DATASET_PATH)
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]
data = data.drop_duplicates().reset_index(drop=True)

X = data.drop(columns=["prognosis"])
y = data["prognosis"]

print("Unique rows:", len(data))
print("Diseases:", y.nunique())

# Check whether every disease has enough samples for 5-fold validation.
counts = y.value_counts()
if counts.min() < 5:
    raise ValueError(
        "Some diseases have fewer than 5 unique patterns. "
        "Five-fold stratified validation is not suitable."
    )

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42,
)

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1,
)

print("\nRunning 5-fold cross-validation...")

results = cross_validate(
    model,
    X,
    y,
    cv=cv,
    scoring={
        "accuracy": "accuracy",
        "macro_f1": "f1_macro",
    },
    n_jobs=-1,
    error_score="raise",
)

accuracy_scores = results["test_accuracy"] * 100
f1_scores = results["test_macro_f1"]

print("\nFold-by-fold results:")
for fold, (accuracy, f1) in enumerate(
    zip(accuracy_scores, f1_scores), start=1
):
    print(
        f"Fold {fold}: Accuracy = {accuracy:.2f}%, "
        f"Macro F1 = {f1:.3f}"
    )

print("\nMean accuracy:", round(accuracy_scores.mean(), 2), "%")
print("Accuracy standard deviation:", round(accuracy_scores.std(), 2))
print("Mean macro F1:", round(f1_scores.mean(), 3))

report = pd.DataFrame({
    "Fold": range(1, 6),
    "Accuracy (%)": accuracy_scores,
    "Macro F1": f1_scores,
})

output_path = PROJECT_DIR / "ai_model" / "random_forest_repeated_results.csv"
report.to_csv(output_path, index=False)

print("\nResults saved to:", output_path)
print("The saved disease_model.pkl was not changed.")
print("This experiment is not clinical validation.")
