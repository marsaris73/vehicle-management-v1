import sqlite3
from datetime import datetime, timedelta
from dashboard_logic import get_dashboard_data
from email_utils import send_notifications

DB_NAME = "fleet.db"


def should_send_email():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_sent TEXT
        )
    """)

    row = c.execute("SELECT last_sent FROM email_log ORDER BY id DESC LIMIT 1").fetchone()

    today = datetime.now().date()

    if not row:
        return True

    last_sent = datetime.strptime(row[0], "%Y-%m-%d").date()

    return last_sent < today


def send_daily_email_if_needed():

    if not should_send_email():
        return

    data, warnings = get_dashboard_data()

    if warnings:
        send_notifications(warnings)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("INSERT INTO email_log (last_sent) VALUES (?)",
              (datetime.now().strftime("%Y-%m-%d"),))

    conn.commit()
    conn.close()
