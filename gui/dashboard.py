# gui/dashboard.py
import tkinter as tk
from tkinter import ttk
from analytics import visualizer, stats
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DashboardFrame(ttk.Frame):
    def __init__(self, master, on_close=None):
        super().__init__(master)
        self.on_close = on_close

        # Title
        ttk.Label(self, text="📊 Expense Dashboard", font=("Arial", 16, "bold")).pack(pady=10)

        # --- Stats Section ---
        insights = stats.get_insights()

        stats_frame = ttk.LabelFrame(self, text="Quick Stats")
        stats_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(stats_frame, text=f"Total Spent: ₹{insights.get('total_spent', 0.0):.2f}").grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(stats_frame, text=f"Top Category: {insights.get('top_category', 'N/A')}").grid(row=1, column=0, padx=5, pady=2)
        ttk.Label(stats_frame, text=f"Highest Expense: ₹{insights.get('highest_expense', 0.0):.2f}").grid(row=2, column=0, padx=5, pady=2)

        # --- Charts Section ---
        charts_frame = ttk.Frame(self)
        charts_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Pie Chart
        pie_fig = visualizer.category_pie()
        pie_canvas = FigureCanvasTkAgg(pie_fig, master=charts_frame)
        pie_canvas.draw()
        pie_canvas.get_tk_widget().grid(row=0, column=0, padx=5, pady=5)

        # Monthly Trend
        trend_fig = visualizer.monthly_trend()
        trend_canvas = FigureCanvasTkAgg(trend_fig, master=charts_frame)
        trend_canvas.draw()
        trend_canvas.get_tk_widget().grid(row=0, column=1, padx=5, pady=5)

        # Back button if `on_close` is provided
        if self.on_close:
            ttk.Button(self, text="⬅ Back", command=self.on_close).pack(pady=10)

    def _mount_matplotlib(self, fig, parent):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        return canvas.get_tk_widget()
