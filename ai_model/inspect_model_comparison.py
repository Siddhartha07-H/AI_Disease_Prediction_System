
from pathlib import Path

import pandas as pd

# Project folder
PROJECT_DIR = Path(__file__).resolve().parent

# Experiment result files
files_to_check = [
    "model_comparison.csv",
    "cross_validation_results.csv",
    "class_distribution.csv",
]

print("=" * 55)
print("AI DISEASE MODEL COMPARISON INSPECTION")
print("=" * 55)

for filename in files_to_check:
    file_path = PROJECT_DIR / filename

    print(f"\nFile: {filename}")

    if not file_path.exists():
        print("Status: File not found. Skipping.")
        continue

    try:
        data = pd.read_csv(file_path)

        print("Status: Read successfully.")
        print("Rows:", len(data))
        print("Columns:", list(data.columns))
        print("\nFirst 10 rows:")
        print(data.head(10).to_string(index=False))

    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as error:
        print("Could not read this file:", error)

print("\n" + "=" * 55)
print("Inspection completed.")
print("No model or experiment files were changed.")
print("=" * 55)
