
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "ai_model" / "disease_model.pkl"

def main():
    model = joblib.load(MODEL_PATH)
    features = list(model.feature_names_in_)

    test_cases = [
        ["itching", "skin_rash"],
        ["cough", "high_fever"],
        ["joint_pain", "muscle_pain"],
        ["itching", "skin_rash", "nodal_skin_eruptions"],
    ]

    print("Testing symptom combinations")
    print("This test does not modify the saved model.\n")

    for symptoms in test_cases:
        unknown = [s for s in symptoms if s not in features]

        if unknown:
            print(f"Skipped {symptoms}: unknown features {unknown}")
            continue

        sample = pd.DataFrame(0, index=[0], columns=features)
        sample.loc[0, symptoms] = 1

        prediction = model.predict(sample)[0]

        print("Symptoms:", ", ".join(symptoms))
        print("Model prediction:", prediction)
        print("-" * 50)

if __name__ == "__main__":
    main()
