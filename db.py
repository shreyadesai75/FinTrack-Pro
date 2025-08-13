import sqlite3
from contextlib import closing
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os
from utils import get_next_id,save_data,load_data
from ml.model import train_model
DB_NAME = "expenses.db" 


def _get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_total_spent_for_month(month_str):
    """
    Returns the total spent for a given month in format YYYY-MM.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(amount) FROM expenses
        WHERE strftime('%Y-%m', date) = ?
    """, (month_str,))
    total = cursor.fetchone()[0]
    conn.close()
    return total or 0.0

def get_monthly_category_totals(month_str):
    """
    Returns a dictionary {category: total_amount} for the given month (YYYY-MM).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, SUM(amount) FROM expenses
        WHERE strftime('%Y-%m', date) = ?
        GROUP BY category
    """, (month_str,))
    data = cursor.fetchall()
    conn.close()
    return {category: total for category, total in data}

def get_total_budget():
    """
    Returns the total budget (sum of all category budgets).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM budgets")
    total = cursor.fetchone()[0]
    conn.close()
    return total or 0.0

def init_db():
    """Create tables if they don't exist."""
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                limit_amount REAL NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.commit()


# ---------- Expense CRUD ----------

def add_expense(date, amount, category, description):
    """Insert a new expense into the SQLite database."""
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO expenses (date, amount, category, description)
            VALUES (?, ?, ?, ?)
            """,
            (date, float(amount), category.strip(), description),
        )
        conn.commit()
        new_id = cur.lastrowid

    # Retrain model if category is provided (Stage 4)
    if category and category.strip():
        from ml.model import train_model
        csv_path = os.path.join("ml", "data.csv")
        if os.path.exists(csv_path):
            train_model(extra_csv_path=csv_path)
        else:
            train_model()

    return new_id


def get_expenses_for_month(year_month: str):
    """Return list of rows (dicts) for expenses in YYYY-MM."""
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, date, amount, category, description FROM expenses WHERE date LIKE ? ORDER BY date ASC, id ASC",
            (f"{year_month}%",),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def get_monthly_category_totals(year_month: str):
    """Return dict {category: total} for given YYYY-MM."""
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT LOWER(category) AS cat, COALESCE(SUM(amount),0) AS total "
            "FROM expenses WHERE date LIKE ? GROUP BY LOWER(category)",
            (f"{year_month}%",),
        )
        out = {}
        for row in cur.fetchall():
            out[row["cat"]] = float(row["total"])
        return out

def get_monthly_series(months_back: int = 6):
    """
    Return list of (YYYY-MM, total) for the last `months_back` months, oldest -> newest.
    """
    from datetime import date
    today = date.today()
    ym_list = []
    y, m = today.year, today.month
    for _ in range(months_back):
        ym_list.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    ym_list.reverse()

    out = []
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        for (yy, mm) in ym_list:
            ym = f"{yy:04d}-{mm:02d}"
            cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM expenses WHERE date LIKE ?", (f"{ym}%",))
            total = float(cur.fetchone()["total"])
            out.append((ym, total))
    return out

def get_all_expenses() -> List[Dict]:
    """Return all expenses as list of dicts, ordered by id."""
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, date, amount, category, description FROM expenses ORDER BY id ASC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def get_expense_by_id(expense_id: int) -> Optional[Dict]:
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, date, amount, category, description FROM expenses WHERE id = ?", (expense_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def update_expense(expense_id: int, date: str, amount: float, category: str, description: str) -> bool:
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE expenses SET date = ?, amount = ?, category = ?, description = ? WHERE id = ?",
            (date, float(amount), category.strip(), description, expense_id),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_expense(expense_id: int) -> bool:
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return cur.rowcount > 0


# ---------- Budget helpers ----------

TOTAL_BUDGET_KEY = "__TOTAL_BUDGET__"


def set_category_budget(category: str, limit_amount: float) -> None:
    """Insert or update budget for a category. Stores category normalized (lowercase)."""
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cat_norm = category.strip().lower()
        cur.execute(
            "INSERT INTO budgets (category, limit_amount) VALUES (?, ?) "
            "ON CONFLICT(category) DO UPDATE SET limit_amount = excluded.limit_amount",
            (cat_norm, float(limit_amount)),
        )
        conn.commit()


def get_category_budget(category: str) -> Optional[float]:
    """Return the budget limit for a specific category, or None if not set."""
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        # we stored budgets in lowercase; query case-insensitively to be safe
        cur.execute("SELECT limit_amount FROM budgets WHERE LOWER(category) = LOWER(?)", (category.strip(),))
        row = cur.fetchone()
        return float(row["limit_amount"]) if row else None


def delete_category_budget(category: str) -> bool:
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM budgets WHERE LOWER(category) = LOWER(?)", (category.strip(),))
        conn.commit()
        return cur.rowcount > 0


def get_all_budgets() -> List[Tuple[str, float]]:
    """Return all budgets (category, limit_amount). category is returned as stored (lowercase)."""
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT category, limit_amount FROM budgets ORDER BY category COLLATE NOCASE")
        rows = cur.fetchall()
        return [(r["category"], float(r["limit_amount"])) for r in rows]


# total budget storage in meta table (key, value)
def set_total_budget(limit_amount: float) -> None:
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (TOTAL_BUDGET_KEY, str(float(limit_amount))),
        )
        conn.commit()


def get_total_budget() -> Optional[float]:
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM meta WHERE key = ?", (TOTAL_BUDGET_KEY,))
        row = cur.fetchone()
        return float(row["value"]) if row else None


# ---------- Aggregation / Month calculations ----------

def _month_from_date(date_text: str) -> str:
    """Return YYYY-MM portion (assumes date_text is YYYY-MM-DD)."""
    try:
        dt = datetime.strptime(date_text, "%Y-%m-%d")
        return dt.strftime("%Y-%m")
    except Exception:
        return date_text[:7]


def get_total_spent_for_month(year_month: str) -> float:
    """year_month should be 'YYYY-MM'"""
    pattern = f"{year_month}%"
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE date LIKE ?", (pattern,))
        return float(cur.fetchone()["total"])


def get_category_spent_for_month(category: str, year_month: str) -> float:
    """Sum spent for a category in a month (case-insensitive category match)."""
    pattern = f"{year_month}%"
    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE LOWER(category) = LOWER(?) AND date LIKE ?",
            (category.strip(), pattern),
        )
        return float(cur.fetchone()["total"])


# ---------- Budget check helper ----------

def check_budget_alerts_for_new_or_update(category: str, amount: float, date: str, ignoring_expense_id: Optional[int] = None) -> List[str]:
    """
    Check whether adding/updating an expense of amount on date for category
    would exceed category or total budgets for that month.
    """
    alerts = []
    year_month = _month_from_date(date)

    with closing(_get_conn()) as conn:
        cur = conn.cursor()
        if ignoring_expense_id:
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE date LIKE ? AND id != ?",
                (f"{year_month}%", ignoring_expense_id),
            )
            total_month = float(cur.fetchone()["total"])
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE LOWER(category) = LOWER(?) AND date LIKE ? AND id != ?",
                (category.strip(), f"{year_month}%", ignoring_expense_id),
            )
            category_month = float(cur.fetchone()["total"])
        else:
            cur.execute("SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE date LIKE ?", (f"{year_month}%",))
            total_month = float(cur.fetchone()["total"])
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE LOWER(category) = LOWER(?) AND date LIKE ?",
                (category.strip(), f"{year_month}%"),
            )
            category_month = float(cur.fetchone()["total"])

    total_budget = get_total_budget()
    category_budget = get_category_budget(category)

    # Evaluate projected totals after adding the new/updated amount
    proj_total = total_month + float(amount)
    proj_category = category_month + float(amount)

    if total_budget is not None and proj_total > total_budget:
        alerts.append(f"Total monthly budget exceeded: {proj_total:.2f} / {total_budget:.2f}")
    if category_budget is not None and proj_category > category_budget:
        alerts.append(f"Category '{category}' budget exceeded: {proj_category:.2f} / {category_budget:.2f}")

    return alerts