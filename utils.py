import json
from datetime import datetime
from typing import List, Dict, Optional

STORAGE_FILE = "expenses.json"


def load_data() -> List[Dict]:
    """Load the list of expenses from STORAGE_FILE. If file is missing or invalid, return empty list."""
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except FileNotFoundError:
        # File doesn't exist yet — caller can create it on save
        return []
    except json.JSONDecodeError:
        print("Warning: expenses.json is corrupted or invalid JSON. Starting with empty list.")
    return []


def save_data(expenses: List[Dict]) -> None:
    """Save the list of expenses to STORAGE_FILE with pretty formatting."""
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2, ensure_ascii=False)


def get_next_id(expenses: List[Dict]) -> int:
    """Return the next integer ID for a new expense (1-based)."""
    if not expenses:
        return 1
    max_id = max((e.get("id", 0) for e in expenses), default=0)
    return max_id + 1


def find_expense_by_id(expenses: List[Dict], expense_id: int) -> Optional[Dict]:
    """Return the expense dict with given id or None."""
    for e in expenses:
        if e.get("id") == expense_id:
            return e
    return None


def add_expense(expenses: List[Dict], date: str, amount: float, description: str, category: str) -> Dict:
    """Create and append a new expense. Returns the new expense."""
    new = {
        "id": get_next_id(expenses),
        "date": date,
        "amount": float(amount),
        "description": description,
        "category": category,
    }
    expenses.append(new)
    save_data(expenses)
    return new


def edit_expense(expenses: List[Dict], expense_id: int, **fields) -> bool:
    """Update fields on an expense. Returns True if updated, False if not found."""
    e = find_expense_by_id(expenses, expense_id)
    if not e:
        return False
    # Only update provided fields (no None)
    for k, v in fields.items():
        if v is not None:
            if k == "amount":
                e[k] = float(v)
            else:
                e[k] = v
    save_data(expenses)
    return True


def delete_expense(expenses: List[Dict], expense_id: int) -> bool:
    """Remove expense by id. Returns True if removed, False if not found."""
    e = find_expense_by_id(expenses, expense_id)
    if not e:
        return False
    expenses.remove(e)
    save_data(expenses)
    return True


# Validation helpers
def validate_date(value: str) -> bool:
    """Validate YYYY-MM-DD format."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_amount(value: str) -> Optional[float]:
    """Return float(amount) if valid positive number, else None."""
    try:
        amt = float(value)
        if amt <= 0:
            return None
        return amt
    except (ValueError, TypeError):
        return None
