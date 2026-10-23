"""
Unit tests for AI Disease Prediction Models
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "ai_model" / "disease_model.pkl"
TRAIN_PATH = ROOT_DIR / "datasets" / "Training.csv"


def test_model_file_exists():
    assert MODEL_PATH.exists(), f"Model file missing at {MODEL_PATH}"


def test_dataset_exists():
    assert TRAIN_PATH.exists(), f"Training dataset missing at {TRAIN_PATH}"


def test_model_features_match_dataset():
    model = joblib.load(MODEL_PATH)
    train_df = pd.read_csv(TRAIN_PATH)
    train_df = train_df.loc[:, ~train_df.columns.astype(str).str.startswith("Unnamed")]

    symptoms = train_df.drop(columns=["prognosis"]).columns.tolist()
    model_features = list(model.feature_names_in_)

    assert len(model_features) == 132
    assert set(model_features) == set(symptoms)


def test_model_prediction_sample():
    model = joblib.load(MODEL_PATH)
    features = list(model.feature_names_in_)

    # Sample: Fungal infection indicators (itching, skin_rash, nodal_skin_eruptions)
    sample_symptoms = ["itching", "skin_rash", "nodal_skin_eruptions"]
    input_vector = pd.DataFrame(
        [[1 if f in sample_symptoms else 0 for f in features]],
        columns=features,
    )

    pred = model.predict(input_vector)[0]
    assert isinstance(pred, str)
    assert len(pred.strip()) > 0
    assert pred.strip() == "Fungal infection"


def test_model_predict_proba():
    model = joblib.load(MODEL_PATH)
    features = list(model.feature_names_in_)

    input_vector = pd.DataFrame(
        [[1 if i < 4 else 0 for i, _ in enumerate(features)]],
        columns=features,
    )

    assert hasattr(model, "predict_proba")
    proba = model.predict_proba(input_vector)[0]
    assert len(proba) == len(model.classes_)
    assert round(float(sum(proba)), 2) == 1.0
