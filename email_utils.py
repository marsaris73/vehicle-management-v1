import sqlite3
import smtplib
from email.mime.text import MIMEText

DB_NAME = "fleet.db"


def get_email_settings():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT sender_email, sender_password, receiver_email FROM settings LIMIT 1")
    settings = c.fetchone()
    conn.close()
    return settings


def send_notifications(messages):
    """
    messages: list of strings
    """

    if not messages:
        return "Δεν υπάρχουν ειδοποιήσεις για αποστολή."

    settings = get_email_settings()

    if not settings:
        return "Δεν έχουν οριστεί ρυθμίσεις email."

    sender, password, receiver = settings

    if not sender or not password or not receiver:
        return "Οι ρυθμίσεις email δεν είναι πλήρεις."

    body = "\n".join(messages)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Fleet Notification Report"
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)

        return "Το email στάλθηκε επιτυχώς."

    except smtplib.SMTPAuthenticationError:
        return "Σφάλμα αυθεντικοποίησης. Έλεγξε το Gmail App Password."

    except Exception as e:
        return f"Σφάλμα αποστολής email: {str(e)}"
