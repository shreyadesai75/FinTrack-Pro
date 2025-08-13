import tkinter as tk
from gui.dashboard import DashboardWindow

root = tk.Tk()
root.withdraw()  # Hide main window
DashboardWindow(root)
root.mainloop()
