import sqlite3
from datetime import datetime
from db import DB_NAME

# -----------------------------
# DB Init for Budgets
# -----------------------------
def init_budget_table():
    """Ensure the budget table exists."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,          -- e.g., '2025-08'
                category TEXT NOT NULL,        -- e.g., 'Food', 'Travel'
                amount REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def set_budget(period, category, amount):
    """Set or update a budget for a specific category and period."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM budgets WHERE period=? AND category=?
        """, (period, category))
        existing = cur.fetchone()
        if existing:
            cur.execute("""
                UPDATE budgets SET amount=? WHERE id=?
            """, (amount, existing[0]))
        else:
            cur.execute("""
                INSERT INTO budgets (period, category, amount, created_at)
                VALUES (?, ?, ?, ?)
            """, (period, category, amount, datetime.now().isoformat()))
        conn.commit()

def get_budget(period, category):
    """Retrieve budget amount for given category and period."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT amount FROM budgets WHERE period=? AND category=?
        """, (period, category))
        row = cur.fetchone()
        return row[0] if row else None

def get_all_budgets(period):
    """Get all category budgets for a period."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT category, amount FROM budgets WHERE period=?
        """, (period,))
        return dict(cur.fetchall())
