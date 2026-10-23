
import pandas as pd

# Load datasets
train = pd.read_csv("datasets/Training.csv")
test = pd.read_csv("datasets/Testing.csv")

print("Before cleaning:")
print("Training shape:", train.shape)
print("Testing shape:", test.shape)

# Remove unnecessary unnamed columns
train = train.loc[:, ~train.columns.str.startswith("Unnamed")]
test = test.loc[:, ~test.columns.str.startswith("Unnamed")]

# Separate symptoms and disease labels
X_train = train.drop(columns=["prognosis"])
y_train = train["prognosis"]

X_test = test.drop(columns=["prognosis"])
y_test = test["prognosis"]

# Check that symptom columns match
if list(X_train.columns) != list(X_test.columns):
    raise ValueError("Training and testing columns do not match!")

print("\nAfter cleaning:")
print("Training features:", X_train.shape)
print("Testing features:", X_test.shape)
print("Number of diseases:", y_train.nunique())
print("Columns match successfully!")

print("\nDataset cleaning completed!")
