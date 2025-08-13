import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from datetime import datetime
import db
from utils import validate_date, validate_amount
from ml.predictor import predict_category
from core.alert_system import run_all_alerts
from ml.anomaly_detector import detect_anomaly
from analytics.stats import get_expense_dataframe
from gui.notifier import show_warning, show_error, system_notify

db.init_db()

class BudgetForm(tk.Toplevel):
    """Popup to set budgets (category budgets + total budget + weekly total)."""

    def __init__(self, master, on_save):
        super().__init__(master)
        self.title("Set Budgets")
        self.resizable(False, False)
        self.on_save = on_save
        pad = {"padx": 10, "pady": 6}

        # Total budget (monthly)
        ttk.Label(self, text="Total Monthly Budget (optional):").grid(row=0, column=0, sticky="w", **pad)
        total = db.get_total_budget()
        self.total_var = tk.StringVar(value=str(total) if total is not None else "")
        ttk.Entry(self, textvariable=self.total_var).grid(row=0, column=1, **pad)

        # Weekly total budget (optional)
        ttk.Label(self, text="Weekly Total Budget (optional):").grid(row=1, column=0, sticky="w", **pad)
        weekly = db.get_weekly_budget()
        self.weekly_var = tk.StringVar(value=str(weekly) if weekly is not None else "")
        ttk.Entry(self, textvariable=self.weekly_var).grid(row=1, column=1, **pad)

        # Category budget
        ttk.Label(self, text="Category:").grid(row=2, column=0, sticky="w", **pad)
        self.cat_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.cat_var).grid(row=2, column=1, **pad)

        ttk.Label(self, text="Category Limit:").grid(row=3, column=0, sticky="w", **pad)
        self.cat_limit_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.cat_limit_var).grid(row=3, column=1, **pad)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        ttk.Button(btn_frame, text="Save Total Budget", command=self.save_total).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Save Weekly Budget", command=self.save_weekly).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Save Category Budget", command=self.save_category).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.destroy).grid(row=0, column=3, padx=5)

        self.budgets_list = tk.Listbox(self, height=6, width=48)
        self.budgets_list.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 10))
        self.refresh_budgets()

        self.grab_set()
        self.transient(master)
        self.wait_visibility()
        self.focus()

    def refresh_budgets(self):
        self.budgets_list.delete(0, tk.END)
        for cat, lim in db.get_all_budgets():
            self.budgets_list.insert(tk.END, f"{cat}: {lim:.2f}")
        total = db.get_total_budget()
        if total is not None:
            self.budgets_list.insert(tk.END, f"__TOTAL__ : {total:.2f}")
        weekly = db.get_weekly_budget()
        if weekly is not None:
            self.budgets_list.insert(tk.END, f"__WEEKLY__ : {weekly:.2f}")

    def save_total(self):
        val = self.total_var.get().strip()
        if val == "":
            db.set_total_budget(0.0)
            messagebox.showinfo("Saved", "Total budget set to 0.0 (treated as no limit).")
            self.refresh_budgets()
            self.on_save()
            return
        if not validate_amount(val):
            messagebox.showerror("Invalid", "Total budget must be a positive number.")
            return
        amt = float(val)
        db.set_total_budget(amt)
        messagebox.showinfo("Saved", f"Total monthly budget set to {amt:.2f}")
        self.refresh_budgets()
        self.on_save()

    def save_weekly(self):
        val = self.weekly_var.get().strip()
        if val == "":
            db.set_weekly_budget(0.0)
            messagebox.showinfo("Saved", "Weekly budget set to 0.0 (treated as no limit).")
            self.refresh_budgets()
            self.on_save()
            return
        if not validate_amount(val):
            messagebox.showerror("Invalid", "Weekly budget must be a positive number.")
            return
        amt = float(val)
        db.set_weekly_budget(amt)
        messagebox.showinfo("Saved", f"Weekly budget set to {amt:.2f}")
        self.refresh_budgets()
        self.on_save()

    def save_category(self):
        cat = self.cat_var.get().strip()
        limit_raw = self.cat_limit_var.get().strip()
        if not cat:
            messagebox.showerror("Invalid", "Category name cannot be empty.")
            return
        if not validate_amount(limit_raw):
            messagebox.showerror("Invalid", "Category limit must be a positive number.")
            return
        amt = float(limit_raw)
        db.set_category_budget(cat, amt)
        messagebox.showinfo("Saved", f"Budget for '{cat}' set to {amt:.2f}")
        self.cat_var.set("")
        self.cat_limit_var.set("")
        self.refresh_budgets()
        self.on_save()


class ExpenseForm(tk.Toplevel):
    """Popup window for adding or editing an expense. Uses db module."""

    def __init__(self, master, on_save, expense: Optional[dict] = None):
        super().__init__(master)
        self.title("Edit Expense" if expense else "Add Expense")
        self.resizable(False, False)
        self.on_save = on_save
        self.expense = expense
        pad = {"padx": 10, "pady": 6}

        # Date
        ttk.Label(self, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", **pad)
        self.date_var = tk.StringVar(value=expense["date"] if expense else datetime.today().strftime("%Y-%m-%d"))
        ttk.Entry(self, textvariable=self.date_var).grid(row=0, column=1, **pad)

        # Amount
        ttk.Label(self, text="Amount:").grid(row=1, column=0, sticky="w", **pad)
        self.amount_var = tk.StringVar(value=str(expense["amount"]) if expense else "")
        ttk.Entry(self, textvariable=self.amount_var).grid(row=1, column=1, **pad)

        # Category + Suggest Button
        ttk.Label(self, text="Category:").grid(row=2, column=0, sticky="w", **pad)
        self.category_var = tk.StringVar(value=expense["category"] if expense else "")
        cat_frame = ttk.Frame(self)
        cat_frame.grid(row=2, column=1, sticky="w", **pad)
        self.category_entry = ttk.Entry(cat_frame, textvariable=self.category_var, width=20)
        self.category_entry.pack(side="left")
        ttk.Button(cat_frame, text="Suggest", command=self.suggest_category).pack(side="left", padx=4)

        # Description
        ttk.Label(self, text="Description:").grid(row=3, column=0, sticky="nw", **pad)
        self.description_text = tk.Text(self, width=30, height=4)
        self.description_text.grid(row=3, column=1, **pad)
        if expense:
            self.description_text.insert("1.0", expense["description"])

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        ttk.Button(btn_frame, text="Save", command=self._on_save).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=1, padx=5)

        self.grab_set()
        self.transient(master)
        self.wait_visibility()
        self.focus()

    def suggest_category(self):
        description = self.description_text.get("1.0", "end").strip()
        amount_raw = self.amount_var.get().strip()
        if not description:
            messagebox.showwarning("Missing description", "Please enter a description first.")
            return
        try:
            amount = float(amount_raw) if amount_raw else 0.0
        except ValueError:
            amount = 0.0
        suggested = predict_category(description, amount)
        if suggested:
            self.category_var.set(suggested)
            messagebox.showinfo("Suggested Category", f"Suggested: {suggested}")
        else:
            messagebox.showinfo("No Suggestion", "Could not predict category.")

    def _on_save(self):
        date = self.date_var.get().strip()
        amount_raw = self.amount_var.get().strip()
        category = self.category_var.get().strip()
        description = self.description_text.get("1.0", "end").strip()

        if not validate_date(date):
            messagebox.showerror("Invalid input", "Date must be in YYYY-MM-DD format.")
            return
        amt = validate_amount(amount_raw)
        if amt is None:
            messagebox.showerror("Invalid input", "Amount must be a positive number.")
            return
        if not category:
            messagebox.showerror("Invalid input", "Category cannot be empty.")
            return
        if not description:
            messagebox.showerror("Invalid input", "Description cannot be empty.")
            return

        ignoring_id = self.expense["id"] if self.expense else None
        alerts = db.check_budget_alerts_for_new_or_update(
            category=category, amount=amt, date=date, ignoring_expense_id=ignoring_id
        )
        if alerts:
            message = "Budget warnings:\n\n" + "\n".join(alerts) + "\n\nDo you want to continue saving?"
            if not messagebox.askyesno("Budget Warning", message):
                return

        if self.expense:
            success = db.update_expense(self.expense["id"], date=date, amount=amt, category=category, description=description)
            if success:
                messagebox.showinfo("Saved", f"Expense {self.expense['id']} updated.")
            else:
                messagebox.showerror("Error", "Failed to update expense (not found).")
        else:
            new_id = db.add_expense(date=date, amount=amt, category=category, description=description)
            messagebox.showinfo("Saved", f"Added expense with ID {new_id}.")
        self.on_save()
        self.destroy()


class FinTrackGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FinTrack Pro")
        self.root.geometry("980x520")
        self._setup_ui()
        self.refresh_table()

        # Show alerts at startup
        self.check_alerts_and_show()

        # Run anomaly detection at startup (already covered via alerts too)
        try:
            df = get_expense_dataframe()
            anomalies = detect_anomaly(df)
            for date, amount in anomalies.items():
                show_warning(f"Unusual spend detected: ₹{amount} on {date}")
        except Exception:
            pass

    def _setup_ui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side="top", fill="x", padx=10, pady=8)
        ttk.Button(top_frame, text="Add Expense", command=self.open_add).pack(side="left", padx=4)
        ttk.Button(top_frame, text="Edit Selected", command=self.open_edit_selected).pack(side="left", padx=4)
        ttk.Button(top_frame, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=4)
        ttk.Button(top_frame, text="Refresh", command=self.refresh_table).pack(side="left", padx=4)
        ttk.Button(top_frame, text="Set Budget", command=self.open_budget_form).pack(side="left", padx=4)
        ttk.Button(top_frame, text="Open Dashboard", command=self.open_dashboard).pack(side="left", padx=10)
        ttk.Button(top_frame, text="Check Alerts", command=self.check_alerts_and_show).pack(side="left", padx=4)

        # Monthly spend meter (progress bar)
        self.progress = ttk.Progressbar(top_frame, length=220, mode="determinate", maximum=100)
        self.progress.pack(side="right", padx=8)
        self.progress_label = ttk.Label(top_frame, text="Budget usage: —")
        self.progress_label.pack(side="right")

        # Main content
        self.content = ttk.Frame(self.root)
        self.content.pack(side="top", fill="both", expand=True)

        # List (expenses) view
        self.list_frame = ttk.Frame(self.content)
        self.list_frame.pack(side="top", fill="both", expand=True)

        columns = ("id", "date", "category", "amount", "description")
        self.tree = ttk.Treeview(self.list_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("date", width=110, anchor="center")
        self.tree.column("category", width=140, anchor="w")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("description", width=520, anchor="w")

        vsb = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))

        self.tree.bind("<Double-1>", lambda e: self.open_edit_selected())

        self.status_var = tk.StringVar()
        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(side="bottom", fill="x", padx=10, pady=6)

        self.dashboard_frame = None

    def close_dashboard(self):
        if self.dashboard_frame is not None:
            self.dashboard_frame.destroy()
            self.dashboard_frame = None
        self.list_frame.pack(side="top", fill="both", expand=True)

    def highlight_anomalies(self, anomalies):
        if not anomalies:
            return
        self.tree.tag_configure("anomaly", background="lightcoral", foreground="white")
        for child in self.tree.get_children():
            values = self.tree.item(child, "values")
            if values and values[1] in anomalies:
                self.tree.item(child, tags=("anomaly",))

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for exp in db.get_all_expenses():
            self.tree.insert("", "end",
                values=(exp["id"], exp["date"], exp["category"], f"{exp['amount']:.2f}", exp["description"])
            )
        self.update_status()

        # Detect anomalies (UI highlight + notif)
        try:
            df = get_expense_dataframe()
            anomalies = detect_anomaly(df)
            for date, amount in anomalies.items():
                msg = f"Unusual spend detected: ₹{amount} on {date}"
                show_warning(msg)
                system_notify("Anomaly", msg)
            self.highlight_anomalies(anomalies)
        except Exception:
            pass

        # Also show tiered budget alerts here
        self.check_alerts_and_show(toast_only=True)

    def check_alerts_and_show(self, toast_only: bool = False):
        """
        Gets alerts and shows them.
        toast_only=True => avoid extra popups; use notifier/system tray.
        """
        alerts = run_all_alerts()
        for alert in alerts:
            t = alert.get("type", "info")
            msg = alert.get("message", "")
            # System tray / notifier always
            system_notify(t.capitalize(), msg)
            # GUI popups depending on severity (or when user clicks button)
            if not toast_only or t in ("danger", "warning"):
                if t == "danger":
                    show_error(msg)
                elif t == "warning":
                    show_warning(msg)
                else:
                    messagebox.showinfo("Info", msg)

    def update_status(self):
        today = datetime.today()
        y_m = today.strftime("%Y-%m")
        total_spent = db.get_total_spent_for_month(y_m)
        total_budget = db.get_total_budget()
        status = f"Month {y_m} — Spent: {total_spent:.2f}"
        if total_budget:
            status += f" / Budget: {total_budget:.2f}"
            if total_spent > total_budget:
                status += "  [OVER BUDGET]"
            # Update progress bar
            pct = min(100.0, (total_spent / total_budget) * 100.0) if total_budget > 0 else 0.0
            self.progress['value'] = pct
            self.progress_label.config(text=f"Budget usage: {pct:.0f}%")
        else:
            self.progress['value'] = 0
            self.progress_label.config(text="Budget usage: —")
        self.status_var.set(status)

    def open_add(self):
        ExpenseForm(self.root, on_save=self.refresh_table)

    def get_selected_expense_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(self.tree.item(sel[0], "values")[0])
        except (ValueError, TypeError):
            return None

    def open_edit_selected(self):
        expense_id = self.get_selected_expense_id()
        if expense_id is None:
            messagebox.showwarning("No selection", "Please select an expense to edit.")
            return
        e = db.get_expense_by_id(expense_id)
        if not e:
            messagebox.showerror("Error", "Selected expense not found.")
            self.refresh_table()
            return
        ExpenseForm(self.root, on_save=self.refresh_table, expense=e)

    def open_dashboard(self):
        if getattr(self, "dashboard_frame", None) is not None:
            return
        self.list_frame.pack_forget()
        from gui.dashboard import DashboardFrame
        self.dashboard_frame = DashboardFrame(self.content, on_close=self.close_dashboard)
        self.dashboard_frame.pack(fill="both", expand=True)

    def delete_selected(self):
        expense_id = self.get_selected_expense_id()
        if expense_id is None:
            messagebox.showwarning("No selection", "Please select an expense to delete.")
            return
        e = db.get_expense_by_id(expense_id)
        if not e:
            messagebox.showerror("Error", "Selected expense not found.")
            self.refresh_table()
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete expense {expense_id}:\n\n{e['description']} ?"):
            return
        if db.delete_expense(expense_id):
            messagebox.showinfo("Deleted", f"Expense {expense_id} deleted.")
        else:
            messagebox.showerror("Error", "Failed to delete expense (not found).")
        self.refresh_table()

    def open_budget_form(self):
        BudgetForm(self.root, on_save=self.refresh_table)

def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use("clam")
    except Exception:
        pass
    FinTrackGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
