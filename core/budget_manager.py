import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Tuple, List
from db import DB_NAME

# --------------------------------------------------------------------
# IMPORTANT:
# This module uses its own table: period_budgets
# Period formats supported:
#   - Monthly: "YYYY-MM"
#   - Weekly (ISO week): "YYYY-Www"  e.g., "2025-W08"
# Category can be any string. For a TOTAL period budget, use "__TOTAL__".
# --------------------------------------------------------------------

TABLE_NAME = "period_budgets"

# Alert thresholds
INFO_THRESHOLD = 0.60
WARNING_THRESHOLD = 0.85
DANGER_THRESHOLD = 1.00


# -----------------------------
# DB Init
# -----------------------------
def init_budget_table() -> None:
    """Ensure the period_budgets table exists."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,          -- '2025-08' or '2025-W08'
                category TEXT NOT NULL,        -- 'Food', '__TOTAL__'
                amount REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


# -----------------------------
# Period helpers
# -----------------------------
def month_key(d: Optional[date] = None) -> str:
    d = d or date.today()
    return f"{d.year:04d}-{d.month:02d}"


def week_key(d: Optional[date] = None) -> str:
    """ISO week period key like '2025-W08'."""
    d = d or date.today()
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year:04d}-W{iso_week:02d}"


def _month_range(ym: str) -> Tuple[str, str]:
    """Given 'YYYY-MM', return (start_date, end_date) inclusive."""
    year, month = map(int, ym.split("-"))
    start = date(year, month, 1)
    # Next month start
    if month == 12:
        next_start = date(year + 1, 1, 1)
    else:
        next_start = date(year, month + 1, 1)
    end = next_start - timedelta(days=1)
    return (start.isoformat(), end.isoformat())


def _week_range(yw: str) -> Tuple[str, str]:
    """Given 'YYYY-Www', return Monday–Sunday date range."""
    try:
        y_str, w_str = yw.split("-W")
        y = int(y_str)
        w = int(w_str)
    except Exception:
        raise ValueError(f"Invalid ISO week period '{yw}'. Expected 'YYYY-Www'.")

    start = date.fromisocalendar(y, w, 1)  # Monday
    end = start + timedelta(days=6)
    return (start.isoformat(), end.isoformat())


def period_range(period: str) -> Tuple[str, str]:
    """Return (start_date, end_date) inclusive for period key."""
    return _week_range(period) if "-W" in period else _month_range(period)


# -----------------------------
# CRUD
# -----------------------------
def set_budget(period: str, category: str, amount: float) -> None:
    """Set or update a budget for a specific category and period."""
    init_budget_table()
    category = category.strip()
    if not period or not category:
        return  # Safety

    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT id FROM {TABLE_NAME} WHERE period=? AND category=?",
            (period, category),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                f"UPDATE {TABLE_NAME} SET amount=? WHERE id=?",
                (float(amount), row[0]),
            )
        else:
            cur.execute(
                f"INSERT INTO {TABLE_NAME} (period, category, amount, created_at) VALUES (?, ?, ?, ?)",
                (period, category, float(amount), datetime.now().isoformat()),
            )
        conn.commit()


def get_budget(period: str, category: str) -> Optional[float]:
    """Retrieve budget amount for given category and period."""
    init_budget_table()
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT amount FROM {TABLE_NAME} WHERE period=? AND category=?",
            (period, category.strip()),
        )
        row = cur.fetchone()
        return float(row[0]) if row else None


def get_all_budgets(period: str) -> Dict[str, float]:
    """Get all category budgets for a period. Returns {category: amount}."""
    init_budget_table()
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT category, amount FROM {TABLE_NAME} WHERE period=?",
            (period,),
        )
        rows = cur.fetchall()
        return {cat: float(amt) for (cat, amt) in rows}


# -----------------------------
# Spending calculations
# -----------------------------
def _sum_expenses_between(start_date: str, end_date: str, category: Optional[str] = None) -> float:
    """Sum expenses in date range; optionally filtered by category."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        if category:
            cur.execute(
                """
                SELECT COALESCE(SUM(amount),0)
                FROM expenses
                WHERE date BETWEEN ? AND ?
                  AND LOWER(category) = LOWER(?)
                """,
                (start_date, end_date, category.strip()),
            )
        else:
            cur.execute(
                """
                SELECT COALESCE(SUM(amount),0)
                FROM expenses
                WHERE date BETWEEN ? AND ?
                """,
                (start_date, end_date),
            )
        total = cur.fetchone()[0]
        return float(total or 0.0)


def get_spent(period: str, category: Optional[str] = None) -> float:
    """Get total spent in a period; optional by category."""
    start, end = period_range(period)
    return _sum_expenses_between(start, end, category)


# -----------------------------
# Threshold status
# -----------------------------
def evaluate_status(used: float, limit: Optional[float]) -> Tuple[str, float]:
    """Return (level, pct) for usage vs limit."""
    if not limit or limit <= 0:
        return ("ok", 0.0)

    pct = used / float(limit)
    if pct >= DANGER_THRESHOLD:
        return ("danger", pct)
    elif pct >= WARNING_THRESHOLD:
        return ("warning", pct)
    elif pct >= INFO_THRESHOLD:
        return ("info", pct)
    else:
        return ("ok", pct)


def build_alert_message(period: str, category: str, used: float, limit: float, level: str) -> str:
    if level == "danger":
        return f"Budget exceeded for '{category}' in {period}: {used:.2f} / {limit:.2f}"
    if level == "warning":
        return f"Approaching budget for '{category}' in {period}: {used:.2f} / {limit:.2f}"
    if level == "info":
        return f"Notice: {category} usage in {period}: {used:.2f} / {limit:.2f}"
    return ""


def summarize_alerts_for_period(period: str) -> List[dict]:
    """
    Build tiered alerts for all budgets in a given period (including '__TOTAL__').
    Returns a list of {type, message}.
    """
    alerts: List[dict] = []
    budgets = get_all_budgets(period)

    # Total budget
    if "__TOTAL__" in budgets:
        limit = budgets["__TOTAL__"]
        used = get_spent(period)
        level, _ = evaluate_status(used, limit)
        if level != "ok":
            alerts.append({
                "type": level,
                "message": build_alert_message(period, "TOTAL", used, limit, level)
            })

    # Category budgets
    for cat, limit in budgets.items():
        if cat == "__TOTAL__":
            continue
        used = get_spent(period, cat)
        level, _ = evaluate_status(used, limit)
        if level != "ok":
            alerts.append({
                "type": level,
                "message": build_alert_message(period, cat, used, limit, level)
            })

    return alerts
