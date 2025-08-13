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
def category_pie():
    """Pie chart of current month's spending by category."""
    ym = datetime.today().strftime("%Y-%m")
    data = db.get_monthly_category_totals(ym)  # dict {category: total}
    labels = list(data.keys()) or ["No data"]
    sizes  = list(data.values()) or [1]

    fig = plt.figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    ax.set_title(f"Category Split — {ym}")
    return fig

def monthly_trend(months_back=6):
    """Line chart of total spending per month for recent months."""
    series = db.get_monthly_series(months_back=months_back)  # list of (YYYY-MM, total)
    xs = [m for m, _ in series]
    ys = [t for _, t in series]

    fig = plt.figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(xs, ys, marker="o")
    ax.set_title("Monthly Spend Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Spent")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig

# -----------------------------
# Standalone plots (optional)
# -----------------------------
def plot_expenses_over_time():
    """Line graph of daily expenses."""
    df = get_expense_dataframe()
    if df.empty:
        print("No expenses to show.")
        return

    daily_totals = df.groupby(df["date"].dt.date)["amount"].sum()
    plt.figure(figsize=(8, 5))
    daily_totals.plot(kind="line", marker="o")
    plt.title("Expenses Over Time")
    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.grid(True)
    plt.show()

def plot_monthly_bar():
    """Bar chart of monthly spending."""
    df = get_expense_dataframe()
    if df.empty:
        print("No expenses to show.")
        return

    df["month"] = df["date"].dt.to_period("M")
    monthly_totals = df.groupby("month")["amount"].sum()
    plt.figure(figsize=(8, 5))
    monthly_totals.plot(kind="bar", color="skyblue")
    plt.title("Monthly Spending")
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
