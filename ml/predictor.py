# ml/predictor.py
import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "category_model.pkl")

def predict_category(description: str, amount: float) -> str:
    """Predict expense category using the trained ML model."""
    if not os.path.exists(MODEL_PATH):
        return None  # Model not trained yet

    model = joblib.load(MODEL_PATH)
    text_input = f"{description} {amount}"
    prediction = model.predict([text_input])
    return prediction[0] if prediction else None
