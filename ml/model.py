# ml/model.py
import os
import sys
from typing import Optional
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "category_model.pkl")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data.csv")


def train_model(extra_csv_path: Optional[str] = None) -> None:
    """
    Train the expense category prediction model using DB data + optional CSV.
    This function imports db functions locally to avoid circular import issues.
    """
    from db import init_db, get_all_expenses  # ✅ Import here to avoid circular import

    # Ensure DB is ready
    init_db()
    expenses = get_all_expenses()
    db_df = pd.DataFrame(expenses)

    if db_df.empty or not {"description", "amount", "category"}.issubset(db_df.columns):
        db_df = pd.DataFrame(columns=["description", "amount", "category"])

    db_df = db_df[["description", "amount", "category"]]

    # Merge with optional CSV
    if extra_csv_path and os.path.exists(extra_csv_path):
        csv_df = pd.read_csv(extra_csv_path)
        csv_df = csv_df[["description", "amount", "category"]]
        data_df = pd.concat([db_df, csv_df], ignore_index=True)
    else:
        data_df = db_df

    # Clean rows
    data_df = data_df.dropna(subset=["description", "category"])
    if data_df.empty:
        raise ValueError("No training data available for category model.")

    # Combine description + amount for text features
    data_df["amount_str"] = data_df["amount"].astype(str)
    X = (data_df["description"].astype(str) + " " + data_df["amount_str"]).tolist()
    y = data_df["category"].astype(str).tolist()

    # Train model
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", MultinomialNB()),
    ])
    pipeline.fit(X, y)

    # Save model
    joblib.dump(pipeline, MODEL_PATH)
    print(f"✅ Model trained and saved to {MODEL_PATH}")


if __name__ == "__main__":
    train_model(extra_csv_path=CSV_PATH if os.path.exists(CSV_PATH) else None)
