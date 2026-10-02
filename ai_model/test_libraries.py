import pandas as pd
import numpy as np
import sklearn

print("AI/ML libraries installed successfully!")

data = {
    "Age": [20, 25, 30, 35],
    "Temperature": [98.6, 99.1, 100.2, 101.0]
}

df = pd.DataFrame(data)

print("\nSample data:")
print(df)

print("\nAverage age:", np.mean(df["Age"]))
print("Scikit-learn version:", sklearn.__version__)