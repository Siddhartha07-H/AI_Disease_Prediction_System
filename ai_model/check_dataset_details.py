
from pathlib import Path
import hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    ROOT / "datasets" / "Training.csv",
    ROOT / "datasets" / "Testing.csv",
]

for file_path in FILES:
    print(f"\nFile: {file_path.name}")

    if not file_path.exists():
        print("File not found")
        continue

    digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
    data = pd.read_csv(file_path)

    print("File size:", file_path.stat().st_size, "bytes")
    print("SHA-256:", digest)
    print("Column count:", len(data.columns))
    print("Last 5 columns:", data.columns[-5:].tolist())

    if "prognosis" in data.columns:
        print("Example disease labels:")
        print(sorted(data["prognosis"].dropna().unique())[:10])
