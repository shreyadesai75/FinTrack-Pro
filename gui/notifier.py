import tkinter as tk
from tkinter import messagebox
from plyer import notification
import threading


def _popup(func, title, message):
    """Run a Tkinter popup in a separate thread so it doesn't block."""
    def run():
        root = tk.Tk()
        root.withdraw()
        func(title, message)
        root.destroy()
    threading.Thread(target=run, daemon=True).start()


def show_warning(message):
    """Show a non-blocking warning popup."""
    _popup(messagebox.showwarning, "Warning", message)


def show_error(message):
    """Show a non-blocking error popup."""
    _popup(messagebox.showerror, "Error", message)


def system_notify(title, message):
    """Show a system tray notification using plyer."""
    try:
        threading.Thread(
            target=lambda: notification.notify(
                title=title,
                message=message,
                timeout=5
            ),
            daemon=True
        ).start()
    except Exception as e:
        print(f"[Notification Error] {e}")
