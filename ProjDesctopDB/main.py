# main.py
import tkinter as tk
from database import ReminderDatabase
from notifications import NotificationManager
from gui import ReminderGUI


def main():
    root = tk.Tk()
    db = ReminderDatabase()
    notifier = NotificationManager(db)
    ReminderGUI(root, db, notifier)
    root.mainloop()


if __name__ == "__main__":
    main()
