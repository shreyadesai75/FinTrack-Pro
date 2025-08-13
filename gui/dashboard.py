# gui/dashboard.py
import tkinter as tk
from tkinter import ttk
from analytics import visualizer, stats
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DashboardFrame(ttk.Frame):
    def __init__(self, master, on_close=None):
        super().__init__(master)
        self.on_close = on_close

        # === FILTER SECTION ===
        filter_frame = ttk.LabelFrame(self, text="Filters")
        filter_frame.pack(fill="x", padx=10, pady=5)

        # Month filter
        ttk.Label(filter_frame, text="Month:").grid(row=0, column=0, padx=5, pady=5)
        self.month_var = tk.StringVar()
        self.month_cb = ttk.Combobox(filter_frame, textvariable=self.month_var, values=["All"], state="readonly")
        self.month_cb.grid(row=0, column=1, padx=5, pady=5)

        # Category filter
        ttk.Label(filter_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5)
        self.cat_var = tk.StringVar()
        self.cat_cb = ttk.Combobox(filter_frame, textvariable=self.cat_var, values=["All"], state="readonly")
        self.cat_cb.grid(row=0, column=3, padx=5, pady=5)

        # Min amount filter
        ttk.Label(filter_frame, text="Min Amount:").grid(row=0, column=4, padx=5, pady=5)
        self.min_amount_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.min_amount_var, width=10).grid(row=0, column=5, padx=5, pady=5)

        # Apply button
        ttk.Button(filter_frame, text="Apply Filters", command=self.refresh_dashboard).grid(row=0, column=6, padx=10)

        # === QUICK STATS SECTION ===
        self.stats_frame = ttk.LabelFrame(self, text="Quick Stats")
        self.stats_frame.pack(fill="x", padx=10, pady=5)

        self.total_label = ttk.Label(self.stats_frame, text="Total Spent: ₹0.00")
        self.total_label.grid(row=0, column=0, padx=5, pady=2)

        self.top_label = ttk.Label(self.stats_frame, text="Top Category: N/A")
        self.top_label.grid(row=1, column=0, padx=5, pady=2)

        self.highest_label = ttk.Label(self.stats_frame, text="Highest Expense: ₹0.00")
        self.highest_label.grid(row=2, column=0, padx=5, pady=2)

        self.avg_label = ttk.Label(self.stats_frame, text="Average Daily: ₹0.00")
        self.avg_label.grid(row=3, column=0, padx=5, pady=2)

        # === CHARTS SECTION ===
        self.charts_frame = ttk.Frame(self)
        self.charts_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Back button
        if self.on_close:
            ttk.Button(self, text="⬅ Back", command=self.on_close).pack(pady=10)

        # Load initial filter values + dashboard
        self.load_filter_values()
        self.refresh_dashboard()

    def load_filter_values(self):
        """Populate filter dropdowns based on DB data."""
        months, categories = stats.get_available_filters()

        self.month_cb["values"] = ["All"] + months
        self.month_cb.current(0)

        self.cat_cb["values"] = ["All"] + categories
        self.cat_cb.current(0)

    def refresh_dashboard(self):
        """Reload stats and charts based on filters."""
        month = None if self.month_var.get() == "All" else self.month_var.get()
        category = None if self.cat_var.get() == "All" else self.cat_var.get()
        try:
            min_amount = float(self.min_amount_var.get()) if self.min_amount_var.get() else None
        except ValueError:
            min_amount = None

        # Update stats
        insights = stats.get_summary_stats(month=month, category=category, min_amount=min_amount)
        self.total_label.config(text=f"Total Spent: ₹{insights['total_spent']:.2f}")
        self.top_label.config(text=f"Top Category: {insights['top_category'] or 'N/A'}")
        self.highest_label.config(text=f"Highest Expense: ₹{insights['highest_spend_amount']:.2f} ({insights['highest_spend'] or 'N/A'})")
        self.avg_label.config(text=f"Average Daily: ₹{insights['average_daily']:.2f}")

        # Clear old charts
        for widget in self.charts_frame.winfo_children():
            widget.destroy()

        # Draw charts with filters
        pie_fig = visualizer.category_pie(month=month, category=category, min_amount=min_amount)
        pie_canvas = FigureCanvasTkAgg(pie_fig, master=self.charts_frame)
        pie_canvas.draw()
        pie_canvas.get_tk_widget().grid(row=0, column=0, padx=5, pady=5)

        trend_fig = visualizer.monthly_trend(months_back=6, category=category, min_amount=min_amount)
        trend_canvas = FigureCanvasTkAgg(trend_fig, master=self.charts_frame)
        trend_canvas.draw()
        trend_canvas.get_tk_widget().grid(row=0, column=1, padx=5, pady=5)
