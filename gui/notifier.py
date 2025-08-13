"""
gui/notifier.py
---------------
Non-blocking UI and system notifications for the expense tracker.
Supports:
    - Tkinter popups (warning/error)
    - System tray notifications via plyer
"""

import tkinter as tk
from tkinter import messagebox
from plyer import notification
import threading


def _show_popup(popup_func, title: str, message: str) -> None:
    """
    Show a Tkinter popup in a separate thread so it won't block the main GUI.
    popup_func: messagebox function (e.g., showwarning, showerror)
    """
    def run():
        try:
            root = tk.Tk()
            root.withdraw()  # Hide main window
            popup_func(title, message)
        except Exception as e:
            print(f"[Popup Error] {e}")
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    threading.Thread(target=run, daemon=True).start()


def show_warning(message: str) -> None:
    """Display a non-blocking warning popup."""
    _show_popup(messagebox.showwarning, "Warning", message)


def show_error(message: str) -> None:
    """Display a non-blocking error popup."""
    _show_popup(messagebox.showerror, "Error", message)


def system_notify(title: str, message: str, timeout: int = 5) -> None:
    """
    Show a system tray notification using plyer in a separate thread.
    timeout: seconds before notification disappears (if supported).
    """
    def notify():
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=timeout
            )
        except Exception as e:
            print(f"[Notification Error] {e}")

    threading.Thread(target=notify, daemon=True).start()
