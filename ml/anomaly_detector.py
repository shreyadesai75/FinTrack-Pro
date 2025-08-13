"""
core/anomaly_detector.py
------------------------
Detect unusual spending patterns using statistical methods.
Supports:
    - Z-score (default)
    - IQR method (optional)
"""

import pandas as pd


def detect_anomaly(expense_df: pd.DataFrame, method: str = "zscore", sensitivity: float = 2.0):
    """
    Detect anomalies in expense data.
    
    Parameters
    ----------
    expense_df : pd.DataFrame
        Must have columns:
            'date'  -> YYYY-MM-DD string
            'amount' -> numeric
    method : str
        "zscore" (mean ± sensitivity*std) or "iqr" (Tukey method)
    sensitivity : float
        For z-score: number of standard deviations above mean.
        For iqr: multiplier for IQR range (default 1.5 typical for outliers).

    Returns
    -------
    list[dict]
        Each dict = {
            "date": str,
            "amount": float,
            "reason": str
        }
    """
    if expense_df.empty or "date" not in expense_df or "amount" not in expense_df:
        return []

    # Aggregate daily totals
    daily_totals = expense_df.groupby("date")["amount"].sum()

    anomalies = []

    if method == "zscore":
        mean_val = daily_totals.mean()
        std_val = daily_totals.std()
        if std_val == 0:
            return []
        threshold = mean_val + sensitivity * std_val
        flagged = daily_totals[daily_totals > threshold]
        for date, amount in flagged.items():
            anomalies.append({
                "date": date,
                "amount": float(amount),
                "reason": f"High spend (>{sensitivity}σ)"
            })

    elif method == "iqr":
        q1 = daily_totals.quantile(0.25)
        q3 = daily_totals.quantile(0.75)
        iqr = q3 - q1
        upper_bound = q3 + sensitivity * iqr
        flagged = daily_totals[daily_totals > upper_bound]
        for date, amount in flagged.items():
            anomalies.append({
                "date": date,
                "amount": float(amount),
                "reason": f"High spend (>{sensitivity}×IQR)"
            })

    return anomalies
