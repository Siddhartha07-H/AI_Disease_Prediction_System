
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.metrics import make_scorer, f1_score

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "datasets" / "Training.csv"

data = pd.read_csv(DATA_PATH)

# Remove unnecessary columns and duplicate rows
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]
data = data.drop_duplicates().reset_index(drop=True)

X = data.drop(columns=["prognosis"])
y = data["prognosis"]

# Five folds; each fold preserves disease proportions
cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

models = {
    "Decision Tree": DecisionTreeClassifier(random_state=42),
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42
    ),
    "Extra Trees": ExtraTreesClassifier(
        n_estimators=200,
        random_state=42
    ),
}

scoring = {
    "accuracy": "accuracy",
    "macro_f1": make_scorer(
        f1_score,
        average="macro",
        zero_division=0
    ),
}

results = []

for name, model in models.items():
    scores = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=scoring,
        n_jobs=-1
    )

    results.append({
        "Model": name,
        "Mean accuracy (%)": round(
            scores["test_accuracy"].mean() * 100, 2
        ),
        "Accuracy standard deviation (%)": round(
            scores["test_accuracy"].std() * 100, 2
        ),
        "Mean macro F1": round(
            scores["test_macro_f1"].mean(), 3
        ),
    })

results_df = pd.DataFrame(results).sort_values(
    "Mean macro F1",
    ascending=False
)

output_path = ROOT_DIR / "ai_model" / "cross_validation_results.csv"
results_df.to_csv(output_path, index=False)

print("\n5-fold cross-validation results:")
print(results_df.to_string(index=False))
print(f"\nResults saved to: {output_path}")
print("Existing disease_model.pkl was not changed.")
print("These results are not clinical validation.")
