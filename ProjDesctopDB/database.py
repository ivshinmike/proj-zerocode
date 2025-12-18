# database.py
import sqlite3
from datetime import datetime, timedelta


class ReminderDatabase:
    def __init__(self, db_path="reminders.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.initdatabase()

    def initdatabase(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_time TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        self.conn.commit()

    def add_reminder(self, title, description, due_time):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO reminders (title, description, due_time, status, created_at)
        VALUES (?, ?, ?, 'Ожидает', ?)
        """, (title, description, due_time, self._now()))
        self.conn.commit()

    def get_all_reminders(self):
        return self.conn.execute(
            "SELECT * FROM reminders ORDER BY due_time"
        ).fetchall()

    def get_due_reminders(self):
        return self.conn.execute("""
        SELECT * FROM reminders
        WHERE status='Ожидает' AND due_time <= ?
        """, (self._now(),)).fetchall()

    def sort_by_due_time(self):
        return self.get_all_reminders()

    def update_status(self, reminder_id, status):
        self.conn.execute("""
        UPDATE reminders SET status=?
        WHERE id=?
        """, (status, reminder_id))
        self.conn.commit()

    def delete_reminder(self, reminder_id):
        self.conn.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
        self.conn.commit()

    def mark_overdue(self):
        overdue_time = (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
        self.conn.execute("""
        UPDATE reminders SET status='Просрочено'
        WHERE status='Ожидает' AND due_time < ?
        """, (overdue_time,))
        self.conn.commit()

    def get_reminder_by_id(self, reminder_id):
        return self.conn.execute(
            "SELECT * FROM reminders WHERE id=?",
            (reminder_id,)
        ).fetchone()

    def get_reminders_count(self):
        return self.conn.execute(
            "SELECT COUNT(*) FROM reminders"
        ).fetchone()[0]

    @staticmethod
    def _now():
        return datetime.now().strftime("%Y-%m-%d %H:%M")


