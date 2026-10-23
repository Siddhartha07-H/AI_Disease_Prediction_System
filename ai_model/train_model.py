
import pandas as pd
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load datasets
train = pd.read_csv("datasets/Training.csv")
test = pd.read_csv("datasets/Testing.csv")

# Remove unnecessary columns
train = train.loc[:, ~train.columns.str.startswith("Unnamed")]
test = test.loc[:, ~test.columns.str.startswith("Unnamed")]

# Separate symptoms and disease labels
X_train = train.drop(columns=["prognosis"])
y_train = train["prognosis"]

X_test = test.drop(columns=["prognosis"])
y_test = test["prognosis"]

# Create the model
model = DecisionTreeClassifier(random_state=42)

# Train the model
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, predictions)

print("Model training completed!")
print("Accuracy:", round(accuracy * 100, 2), "%")
print("\nClassification report:")
print(classification_report(y_test, predictions))

# Save the trained model
joblib.dump(model, "ai_model/disease_model.pkl")

print("\nModel saved successfully!")
