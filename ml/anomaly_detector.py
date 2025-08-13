import pandas as pd

def detect_anomaly(expense_df):
    """
    Detect anomalies using z-score.
    expense_df must have 'date' (YYYY-MM-DD) and 'amount' columns.
    Returns: dict {date: amount}
    """
    if expense_df.empty:
        return {}

    daily_totals = expense_df.groupby("date")["amount"].sum()
    mean_val = daily_totals.mean()
    std_val = daily_totals.std()

    if std_val == 0:
        return {}

    threshold = mean_val + 2 * std_val
    flagged = daily_totals[daily_totals > threshold]

    return flagged.to_dict()
