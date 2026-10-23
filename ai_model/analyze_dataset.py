
import pandas as pd

# Load both datasets
train = pd.read_csv("datasets/Training.csv")
test = pd.read_csv("datasets/Testing.csv")

print("TRAINING DATA")
print("Shape:", train.shape)
print("Missing values:", train.isnull().sum().sum())
print("Duplicate rows:", train.duplicated().sum())

print("\nTESTING DATA")
print("Shape:", test.shape)
print("Missing values:", test.isnull().sum().sum())
print("Duplicate rows:", test.duplicated().sum())

# Check disease distribution
print("\nDISEASE COUNTS")
print(train["prognosis"].value_counts())

# Check columns
print("\nCOLUMN CHECK")
train_columns = set(train.columns)
test_columns = set(test.columns)

print("Columns only in training:",
      train_columns - test_columns)
print("Columns only in testing:",
      test_columns - train_columns)

print("\nDataset analysis completed!")
