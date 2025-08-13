# analytics/stats.py
import pandas as pd
from datetime import datetime
from db import get_all_expenses

# -----------------------------
# Helper to fetch expenses
# -----------------------------
def get_expense_dataframe():
    """Fetch expenses from DB as a pandas DataFrame."""
    expenses = get_all_expenses()
    if not expenses:
        return pd.DataFrame(columns=["date", "amount", "description", "category"])
    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])
    return df

# -----------------------------
# Summary stats with filters
# -----------------------------
def get_available_filters():
    df = get_expense_dataframe()
    if df.empty:
        return [], []
    months = sorted(df["date"].dt.strftime("%Y-%m").unique(), reverse=True)
    categories = sorted(df["category"].dropna().unique())
    return months, categories


def get_summary_stats(month=None, category=None, min_amount=None):
    df = get_expense_dataframe()
    if df.empty:
        return { "total_spent": 0, "top_category": None, "top_category_amount": 0,
                 "highest_spend": None, "highest_spend_amount": 0, "average_daily": 0 }

    # Apply filters
    if month:
        df = df[df["date"].dt.strftime("%Y-%m") == month]
    if category:
        df = df[df["category"] == category]
    if min_amount:
        df = df[df["amount"] >= min_amount]

    if df.empty:
        return { "total_spent": 0, "top_category": None, "top_category_amount": 0,
                 "highest_spend": None, "highest_spend_amount": 0, "average_daily": 0 }

    total_spent = df["amount"].sum()
    category_totals = df.groupby("category")["amount"].sum()
    top_category = category_totals.idxmax()
    top_category_amount = category_totals.max()

    highest_row = df.loc[df["amount"].idxmax()]
    highest_spend_amount = highest_row["amount"]
    highest_spend = f"{highest_row['description']} ({highest_row['category']})"

    daily_avg = df.groupby(df["date"].dt.date)["amount"].sum().mean()

    return {
        "total_spent": round(total_spent, 2),
        "top_category": top_category,
        "top_category_amount": round(top_category_amount, 2),
        "highest_spend": highest_spend,
        "highest_spend_amount": round(highest_spend_amount, 2),
        "average_daily": round(daily_avg, 2)
    }
