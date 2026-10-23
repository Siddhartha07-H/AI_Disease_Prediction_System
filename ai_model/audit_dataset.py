
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

TRAIN_FILE = ROOT / "datasets" / "Training.csv"
TEST_FILE = ROOT / "datasets" / "Testing.csv"

def inspect_file(file_path):
    print(f"\n--- {file_path.name} ---")

    data = pd.read_csv(file_path)

    # Remove unnecessary unnamed columns for inspection only.
    data = data.loc[
        :, ~data.columns.astype(str).str.startswith("Unnamed")
    ]

    print("Rows:", data.shape[0])
    print("Columns:", data.shape[1])
    print("Missing values:", int(data.isnull().sum().sum()))
    print("Duplicate rows:", int(data.duplicated().sum()))

    if "prognosis" in data.columns:
        print("Disease labels:", data["prognosis"].nunique())
        print("\nDisease examples:")
        print(data["prognosis"].value_counts().head(10).to_string())

        if "prognosis" in data.columns:
            print("\nTarget column: prognosis")
    else:
        print("WARNING: prognosis column not found")

    print("\nFirst 10 column names:")
    print(data.columns[:10].tolist())

def main():
    print("DATASET AUDIT")
    print("This script only reads the CSV files.")
    print("It does not modify your dataset or models.")

    for file_path in [TRAIN_FILE, TEST_FILE]:
        if file_path.exists():
            inspect_file(file_path)
        else:
            print(f"\nFile not found: {file_path}")

if __name__ == "__main__":
    main()
