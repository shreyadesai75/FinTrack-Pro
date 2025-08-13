# gui/components/expense_form.py
import tkinter as tk
from tkinter import ttk
from ml.predictor import predict_category

class ExpenseForm(tk.Frame):
    def __init__(self, master, on_submit):
        super().__init__(master)
        self.on_submit = on_submit

        tk.Label(self, text="Date (YYYY-MM-DD):").grid(row=0, column=0)
        self.date_entry = tk.Entry(self)
        self.date_entry.grid(row=0, column=1)

        tk.Label(self, text="Amount:").grid(row=1, column=0)
        self.amount_entry = tk.Entry(self)
        self.amount_entry.grid(row=1, column=1)

        tk.Label(self, text="Description:").grid(row=2, column=0)
        self.desc_entry = tk.Entry(self)
        self.desc_entry.grid(row=2, column=1)
        self.desc_entry.bind("<FocusOut>", self.auto_suggest_category)  # Trigger on leaving field

        tk.Label(self, text="Category:").grid(row=3, column=0)
        self.category_entry = tk.Entry(self)
        self.category_entry.grid(row=3, column=1)

        self.submit_btn = tk.Button(self, text="Add Expense", command=self.submit)
        self.submit_btn.grid(row=4, column=0, columnspan=2)

    def auto_suggest_category(self, event=None):
        desc = self.desc_entry.get().strip()
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            amount = 0.0

        if desc and amount > 0:
            suggestion = predict_category(desc, amount)
            if suggestion:
                self.category_entry.delete(0, tk.END)
                self.category_entry.insert(0, suggestion)

    def submit(self):
        date = self.date_entry.get()
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            amount = 0.0
        category = self.category_entry.get()
        description = self.desc_entry.get()

        if self.on_submit:
            self.on_submit(date, amount, category, description)
