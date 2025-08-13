from datetime import datetime
import db
from core import budget_manager
from ml.anomaly_detector import detect_anomaly
import pandas as pd

def run_all_alerts():
    """
    Check:
      - Total monthly budget
      - Category budgets
      - ML anomaly detection (z-score)
    Returns: list of alert dicts: {"type": "info|warning|danger", "message": str}
    """
    alerts = []
    current_month = datetime.today().strftime("%Y-%m")
    print("DEBUG: Current month =", current_month)

    # --- Total budget check ---
    total_budget = db.get_total_budget()
    spent = db.get_total_spent_for_month(current_month)
    print("DEBUG: total_budget =", total_budget, "spent =", spent)

    if total_budget and spent is not None:
        percent = (spent / total_budget) * 100
        if percent >= 100:
            alerts.append({"type": "danger", "message": f"Over total budget! Spent ₹{spent:.2f} of ₹{total_budget:.2f}"})
        elif percent >= 85:
            alerts.append({"type": "warning", "message": f"Approaching total budget limit ({spent:.2f} / {total_budget:.2f})"})
        elif percent >= 60:
            alerts.append({"type": "info", "message": f"60% of total budget reached ({spent:.2f} / {total_budget:.2f})"})

    # --- Category budgets check ---
    all_budgets = budget_manager.get_all_budgets(current_month)
    print("DEBUG: All budgets =", all_budgets)

    for category, limit in all_budgets.items():
        spent_cat = db.get_category_spent_for_month(category, current_month)
        print(f"DEBUG: {category} => limit={limit}, spent={spent_cat}")

        if spent_cat is not None:
            percent_cat = (spent_cat / limit) * 100 if limit else 0
            if percent_cat >= 100:
                alerts.append({"type": "danger", "message": f"Over budget for '{category}': {spent_cat:.2f} / {limit:.2f}"})
            elif percent_cat >= 85:
                alerts.append({"type": "warning", "message": f"Approaching budget for '{category}': {spent_cat:.2f} / {limit:.2f}"})
            elif percent_cat >= 60:
                alerts.append({"type": "info", "message": f"60% of budget for '{category}' reached ({spent_cat:.2f} / {limit:.2f})"})

    # --- ML anomaly detection ---
    expenses = db.get_expenses_for_month(current_month)  # should return list of tuples (date, amount)
    if expenses:
        df = pd.DataFrame(expenses, columns=["date", "amount"])
        anomalies = detect_anomaly(df)
        if anomalies:
            for date, amt in anomalies.items():
                alerts.append({"type": "warning", "message": f"Anomaly detected on {date}: ₹{amt:.2f} (unusually high spend)"})

    return alerts
