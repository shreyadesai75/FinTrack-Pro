# analytics/stats.py
import pandas as pd
from db import get_all_expenses

import db
from datetime import datetime

import db
import datetime

# analytics/stats.py
from datetime import datetime
import calendar
import db

def _current_year_month():
    return datetime.today().strftime("%Y-%m")

def get_insights():
    """Compute summary metrics the dashboard shows."""
    ym = _current_year_month()
    total_spent = db.get_total_spent_for_month(ym)

    # Category totals and top category
    cat_totals = db.get_monthly_category_totals(ym)
    if cat_totals:
        top_category = max(cat_totals, key=cat_totals.get)
    else:
        top_category = "—"

    # Highest single expense (this month)
    month_rows = db.get_expenses_for_month(ym)
    highest = max((r["amount"] for r in month_rows), default=0.0)

    # Avg daily (this month)
    year, month = map(int, ym.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]
    avg_daily = total_spent / days_in_month if days_in_month else 0.0

    # Savings % vs budget (only if total budget set)
    total_budget = db.get_total_budget()
    if total_budget and total_budget > 0:
        savings_percent = (1 - (total_spent / total_budget)) * 100
    else:
        savings_percent = 0.0

    return {
        "total_spent": float(total_spent),
        "top_category": top_category,
        "highest_expense": float(highest),
        "avg_daily": float(avg_daily),
        "savings_percent": float(savings_percent),
    }

def get_expense_dataframe():
    """Fetch expenses from DB as a pandas DataFrame."""
    expenses = get_all_expenses()
    if not expenses:
        return pd.DataFrame(columns=["date", "amount", "description", "category"])
    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])
    return df


def get_summary_stats():
    """Return key stats about expenses."""
    df = get_expense_dataframe()
    if df.empty:
        return {
            "total_spent": 0,
            "top_category": None,
            "top_category_amount": 0,
            "highest_spend": None,
            "highest_spend_amount": 0,
            "average_daily": 0
        }

    total_spent = df["amount"].sum()

    category_totals = df.groupby("category")["amount"].sum()
    if not category_totals.empty:
        top_category = category_totals.idxmax()
        top_category_amount = category_totals.max()
    else:
        top_category = None
        top_category_amount = 0

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
