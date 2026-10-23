
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.metrics import accuracy_score, f1_score

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

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
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

results = []

for name, model in models.items():
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    results.append({
        "Model": name,
        "Accuracy (%)": round(
            accuracy_score(y_test, predictions) * 100, 2
        ),
        "Macro F1": round(
            f1_score(
                y_test,
                predictions,
                average="macro",
                zero_division=0
            ), 3
        )
    })

results_df = pd.DataFrame(results)
results_df = results_df.sort_values(
    by="Macro F1", ascending=False
)

output_path = ROOT_DIR / "ai_model" / "model_comparison.csv"
results_df.to_csv(output_path, index=False)

print("\nModel comparison:")
print(results_df.to_string(index=False))
print(f"\nResults saved to: {output_path}")
print("\nExisting disease_model.pkl was not changed.")
print("This comparison is not clinical validation.")
