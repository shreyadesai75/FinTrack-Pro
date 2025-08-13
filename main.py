import sys
from typing import List, Dict

from utils import (
    load_data,
    save_data,
    add_expense,
    edit_expense,
    delete_expense,
    find_expense_by_id,
    validate_date,
    validate_amount,
)

MENU = """
FinTrack Pro — Stage 1 (Basic CLI)
Choose an option:
1. Add Expense
2. View All Expenses
3. Edit an Expense
4. Delete an Expense
5. Exit
"""


def print_table(expenses: List[Dict]) -> None:
    """Print a simple table of expenses (ID | Date | Category | Amount | Description)."""
    if not expenses:
        print("No expenses found.")
        return

    # Determine column widths (simple)
    id_w = max(2, max(len(str(e["id"])) for e in expenses))
    date_w = max(4, max(len(e["date"]) for e in expenses))
    cat_w = max(8, max(len(e["category"]) for e in expenses))
    amt_w = max(6, max(len(f"{e['amount']:.2f}") for e in expenses))
    desc_w = max(11, max(len(e["description"]) for e in expenses))

    header = f"{'ID':>{id_w}}  {'Date':<{date_w}}  {'Category':<{cat_w}}  {'Amount':>{amt_w}}  Description"
    print(header)
    print("-" * len(header))
    for e in expenses:
        print(
            f"{e['id']:>{id_w}}  {e['date']:<{date_w}}  {e['category']:<{cat_w}}  {e['amount']:>{amt_w}.2f}  {e['description']}"
        )


def prompt_add(expenses: List[Dict]) -> None:
    """Prompt the user to add a new expense."""
    print("\nAdd Expense — enter values (type 'cancel' at any prompt to abort)\n")

    # Date
    while True:
        date = input("Date (YYYY-MM-DD): ").strip()
        if date.lower() == "cancel":
            print("Add cancelled.")
            return
        if validate_date(date):
            break
        print("Invalid date. Please use YYYY-MM-DD.")

    # Amount
    while True:
        amount_raw = input("Amount (positive number): ").strip()
        if amount_raw.lower() == "cancel":
            print("Add cancelled.")
            return
        amount = validate_amount(amount_raw)
        if amount is not None:
            break
        print("Invalid amount. Enter a positive number (e.g. 12.50).")

    # Description
    while True:
        description = input("Description: ").strip()
        if description.lower() == "cancel":
            print("Add cancelled.")
            return
        if description:
            break
        print("Description cannot be empty.")

    # Category
    while True:
        category = input("Category: ").strip()
        if category.lower() == "cancel":
            print("Add cancelled.")
            return
        if category:
            break
        print("Category cannot be empty.")

    new = add_expense(expenses, date=date, amount=amount, description=description, category=category)
    print(f"Added expense with ID {new['id']}.")


def prompt_view(expenses: List[Dict]) -> None:
    print("\nAll Expenses\n")
    # Sort by id ascending for viewing
    sorted_expenses = sorted(expenses, key=lambda x: x["id"])
    print_table(sorted_expenses)
    print("")


def prompt_edit(expenses: List[Dict]) -> None:
    print("\nEdit Expense\n")
    id_raw = input("Enter the ID of the expense to edit (or 'cancel'): ").strip()
    if id_raw.lower() == "cancel":
        print("Edit cancelled.")
        return
    if not id_raw.isdigit():
        print("Invalid ID. Must be an integer.")
        return
    expense_id = int(id_raw)
    e = find_expense_by_id(expenses, expense_id)
    if not e:
        print(f"No expense found with ID {expense_id}.")
        return

    print("Press Enter to keep current value.\n")
    # Date
    while True:
        new_date = input(f"Date [{e['date']}]: ").strip()
        if new_date == "":
            new_date_final = e["date"]
            break
        if validate_date(new_date):
            new_date_final = new_date
            break
        print("Invalid date. Use YYYY-MM-DD.")

    # Amount
    while True:
        new_amount_raw = input(f"Amount [{e['amount']:.2f}]: ").strip()
        if new_amount_raw == "":
            new_amount_final = e["amount"]
            break
        new_amount_valid = validate_amount(new_amount_raw)
        if new_amount_valid is not None:
            new_amount_final = new_amount_valid
            break
        print("Invalid amount. Enter a positive number.")

    # Description
    new_description = input(f"Description [{e['description']}]: ").strip()
    if new_description == "":
        new_description_final = e["description"]
    else:
        new_description_final = new_description

    # Category
    new_category = input(f"Category [{e['category']}]: ").strip()
    if new_category == "":
        new_category_final = e["category"]
    else:
        new_category_final = new_category

    changed = edit_expense(
        expenses,
        expense_id,
        date=new_date_final,
        amount=new_amount_final,
        description=new_description_final,
        category=new_category_final,
    )
    if changed:
        print(f"Expense {expense_id} updated.")
    else:
        print("Failed to update expense (not found).")


def prompt_delete(expenses: List[Dict]) -> None:
    print("\nDelete Expense\n")
    id_raw = input("Enter the ID of the expense to delete (or 'cancel'): ").strip()
    if id_raw.lower() == "cancel":
        print("Delete cancelled.")
        return
    if not id_raw.isdigit():
        print("Invalid ID. Must be an integer.")
        return
    expense_id = int(id_raw)
    e = find_expense_by_id(expenses, expense_id)
    if not e:
        print(f"No expense found with ID {expense_id}.")
        return
    confirm = input(f"Are you sure you want to delete expense {expense_id} ({e['description']})? [y/N]: ").strip().lower()
    if confirm == "y":
        if delete_expense(expenses, expense_id):
            print(f"Expense {expense_id} deleted.")
        else:
            print("Failed to delete (not found).")
    else:
        print("Delete cancelled.")


def main():
    # Load data once at start (functions will save after changes)
    expenses = load_data()

    while True:
        print(MENU)
        choice = input("Enter choice [1-5]: ").strip()

        if choice == "1":
            prompt_add(expenses)
        elif choice == "2":
            prompt_view(expenses)
        elif choice == "3":
            prompt_edit(expenses)
        elif choice == "4":
            prompt_delete(expenses)
        elif choice == "5":
            print("Goodbye — saving and exiting.")
            # save_data is already called by operations, but ensure final save just in case
            try:
                save_data(expenses)
            except Exception:
                pass
            sys.exit(0)
        else:
            print("Invalid choice. Enter a number from 1 to 5.")


if __name__ == "__main__":
    main()
