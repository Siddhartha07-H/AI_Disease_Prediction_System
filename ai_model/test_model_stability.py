
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "datasets" / "Training.csv"

data = pd.read_csv(DATA_PATH)
data = data.loc[
    :, ~data.columns.astype(str).str.startswith("Unnamed")
]
data = data.drop_duplicates().reset_index(drop=True)

X = data.drop(columns=["prognosis"])
y = data["prognosis"]

print("Testing Random Forest stability")
print("Unique rows:", len(data))
print("Diseases:", y.nunique())
print()

results = []

for seed in [7, 21, 42, 77, 123]:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=seed,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions) * 100
    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    results.append({
        "Split seed": seed,
        "Accuracy (%)": round(accuracy, 2),
        "Macro F1": round(macro_f1, 3)
    })

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

print("\nMean accuracy:", round(results_df["Accuracy (%)"].mean(), 2), "%")
print("Mean macro F1:", round(results_df["Macro F1"].mean(), 3))
print("\nExisting disease_model.pkl was not changed.")
print("This experiment is not clinical validation.")
