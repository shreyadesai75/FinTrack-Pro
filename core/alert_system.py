from datetime import datetime
import db

def run_all_alerts():
    """Check total budget, category budgets, and return alert messages."""
    alerts = []

    # Get current month in the same format as your DB
    current_month = datetime.today().strftime("%Y-%m")

    print("DEBUG: Current month =", current_month)  # Debug

    # --- Check total budget ---
    total_budget = db.get_total_budget()
    spent = db.get_total_spent_for_month(current_month)

    print("DEBUG: total_budget =", total_budget, "spent =", spent)  # Debug

    if total_budget and spent is not None:
        if spent > total_budget:
            alerts.append({
                "type": "danger",
                "message": f"Over total budget! Spent ₹{spent:.2f} of ₹{total_budget:.2f}"
            })
        elif spent > total_budget * 0.9:
            alerts.append({
                "type": "warning",
                "message": f"Approaching total budget limit ({spent:.2f} / {total_budget:.2f})"
            })

    # --- Check category budgets ---
    all_budgets = db.get_all_budgets()
    print("DEBUG: All budgets =", all_budgets)  # Debug

    for category, limit in all_budgets:
        spent_cat = db.get_category_spent_for_month(category, current_month)
        print(f"DEBUG: {category} => limit={limit}, spent={spent_cat}")  # Debug

        if spent_cat is not None:
            if spent_cat > limit:
                alerts.append({
                    "type": "danger",
                    "message": f"Over budget for '{category}': {spent_cat:.2f} / {limit:.2f}"
                })
            elif spent_cat > limit * 0.9:
                alerts.append({
                    "type": "warning",
                    "message": f"Approaching budget for '{category}': {spent_cat:.2f} / {limit:.2f}"
                })

    return alerts
