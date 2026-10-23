
import pandas as pd

# Load the training dataset
data = pd.read_csv("datasets/Training.csv")

print("Dataset loaded successfully!")
print("\nFirst 5 rows:")
print(data.head())

print("\nDataset shape:")
print(data.shape)

print("\nColumn names:")
print(data.columns.tolist())

print("\nMissing values:")
print(data.isnull().sum().sum())

print("\nDisease names:")
print(data["prognosis"].unique())

print("\nNumber of diseases:")
print(data["prognosis"].nunique())
