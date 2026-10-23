
import pandas as pd
import joblib

# Load the saved model
model = joblib.load("ai_model/disease_model.pkl")

# Load the training dataset
train = pd.read_csv("datasets/Training.csv")
train = train.loc[:, ~train.columns.str.startswith("Unnamed")]

# Separate symptoms and disease labels
X = train.drop(columns=["prognosis"])
y = train["prognosis"]

# Select one example from the dataset
sample = X.iloc[[0]]
actual_disease = y.iloc[0]

# Predict the disease
predicted_disease = model.predict(sample)[0]

print("Model loaded successfully!")
print("Actual disease:", actual_disease)
print("Predicted disease:", predicted_disease)

if predicted_disease == actual_disease:
    print("Result: Prediction matches the dataset label.")
else:
    print("Result: Prediction does not match the dataset label.")
