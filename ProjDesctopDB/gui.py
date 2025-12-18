# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta


class ReminderGUI:
    def __init__(self, root, db, notifier):
        self.root = root
        self.db = db
        self.notifier = notifier
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Напоминалка")
        self.root.geometry("800x500")

        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="➕ Добавить", command=self.add_reminder).pack(side="left")
        ttk.Button(toolbar, text="🔔 Тест", command=self.notifier.test_notification).pack(side="left")
        ttk.Button(toolbar, text="1 мин", command=lambda: self.set_quick_time(1)).pack(side="left")
        ttk.Button(toolbar, text="5 мин", command=lambda: self.set_quick_time(5)).pack(side="left")
        ttk.Button(toolbar, text="15 мин", command=lambda: self.set_quick_time(15)).pack(side="left")

        self.tree = ttk.Treeview(
            self.root,
            columns=("id", "title", "time", "status"),
            show="headings"
        )
        for col in ("id", "title", "time", "status"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self.on_double_click)

        self.status = ttk.Label(self.root, text="")
        self.status.pack(fill="x")

        self.refresh_reminders()
        self.update_status_bar()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_status_bar(self):
        self.status.config(text=f"Всего напоминаний: {self.db.get_reminders_count()}")

    def refresh_reminders(self):
        self.tree.delete(*self.tree.get_children())
        for r in self.db.get_all_reminders():
            self.tree.insert("", "end", values=(
                r["id"], r["title"], r["due_time"], r["status"]
            ))

    def add_reminder(self):
        title = simple_input("Заголовок")
        if not title:
            return
        desc = simple_input("Описание")
        due = simple_input("Дата и время (YYYY-MM-DD HH:MM)")
        try:
            datetime.strptime(due, "%Y-%m-%d %H:%M")
        except Exception:
            messagebox.showerror("Ошибка", "Неверный формат даты")
            return

        self.db.add_reminder(title, desc, due)
        self.refresh_reminders()
        self.update_status_bar()

    def set_quick_time(self, minutes):
        due = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")
        self.db.add_reminder("Быстрое напоминание", "", due)
        self.refresh_reminders()
        self.update_status_bar()

    def mark_as_done(self, reminder_id):
        self.db.update_status(reminder_id, "Готово")
        self.refresh_reminders()

    def delete_reminder(self, reminder_id):
        self.db.delete_reminder(reminder_id)
        self.refresh_reminders()
        self.update_status_bar()

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        rid = int(self.tree.item(item)["values"][0])
        r = self.db.get_reminder_by_id(rid)
        messagebox.showinfo(
            "Детали",
            f"{r['title']}\n\n{r['description']}\n\n{r['due_time']}"
        )

    def on_closing(self):
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
            self.notifier.stop()
            self.root.destroy()


def simple_input(title):
    win = tk.Toplevel()
    win.title(title)
    win.geometry("400x120")
    value = tk.StringVar()

    ttk.Entry(win, textvariable=value).pack(pady=10, padx=10, fill="x")
    ttk.Button(win, text="OK", command=win.destroy).pack()

    win.wait_window()
    return value.get()
