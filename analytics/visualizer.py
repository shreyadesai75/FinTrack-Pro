# analytics/visualizer.py
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import db

# -----------------------------
# Helper to fetch expenses as DataFrame
# -----------------------------
def get_expense_dataframe():
    """Fetch expenses from DB as a pandas DataFrame."""
    expenses = db.get_all_expenses()
    if not expenses:
        return pd.DataFrame(columns=["date", "amount", "description", "category"])
    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])
    return df

# -----------------------------
# Charts for dashboard
# -----------------------------
def category_pie(month=None, category=None, min_amount=None):
    df = get_expense_dataframe()
    if month:
        df = df[df["date"].dt.strftime("%Y-%m") == month]
    if category:
        df = df[df["category"] == category]
    if min_amount:
        df = df[df["amount"] >= min_amount]

    if df.empty:
        labels, sizes = ["No data"], [1]
    else:
        category_totals = df.groupby("category")["amount"].sum()
        labels = category_totals.index
        sizes = category_totals.values

    fig = plt.figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    ax.set_title("Category Split")
    return fig


def monthly_trend(months_back=6, category=None, min_amount=None):
    df = get_expense_dataframe()
    if category:
        df = df[df["category"] == category]
    if min_amount:
        df = df[df["amount"] >= min_amount]

    df["month"] = df["date"].dt.to_period("M")
    monthly_totals = df.groupby("month")["amount"].sum().tail(months_back)

    fig = plt.figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(monthly_totals.index.astype(str), monthly_totals.values, marker="o")
    ax.set_title("Monthly Spend Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Spent")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig
