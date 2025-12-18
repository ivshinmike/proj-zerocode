# notifications.py
import threading
import time
import tkinter as tk
from tkinter import ttk

try:
    from win10toast import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False

class NotificationManager:
    def __init__(self, db):
        self.db = db
        self.running = True
        self.toast = ToastNotifier() if TOAST_AVAILABLE else None
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def _monitor(self):
        while self.running:
            self.db.mark_overdue()
            due = self.db.get_due_reminders()
            for r in due:
                self._show_notification(r["title"], r["description"])
                self.db.update_status(r["id"], "Просрочено")
            time.sleep(1)

    def _show_notification(self, title, message):
        if self.toast:
            try:
                self.toast.show_toast(title, message, duration=10, threaded=True)
                return
            except Exception:
                pass
        self._show_popup(title, message)

    def _show_popup(self, title, message):
        win = tk.Toplevel()
        win.title("Напоминание")
        win.attributes("-topmost", True)
        win.geometry("400x200")

        ttk.Label(win, text=title, font=("Segoe UI", 12, "bold")).pack(pady=10)
        ttk.Label(win, text=message, wraplength=380).pack(pady=5)
        ttk.Button(win, text="OK", command=win.destroy).pack(pady=10)

        win.after(30000, win.destroy)

    def show_manual_notification(self, title, message):
        self._show_notification(title, message)

    def test_notification(self):
        self._show_notification("Тест", "Это тестовое уведомление")

    def stop(self):
        self.running = False
