import sqlite3
import os
from datetime import datetime

DB_NAME = "fleet.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# ================= ADD SERVICE =================
def add_service(
    vehicle_id,
    service_date,
    km_done,
    hours_done,
    next_service_date,
    next_service_km,
    next_service_hours,
    cost,
    invoice_file=None
):

    invoice_path = ""

    if invoice_file:
        os.makedirs("documents/service_invoices", exist_ok=True)
        filename = f"{vehicle_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{invoice_file.name}"
        invoice_path = os.path.join("documents/service_invoices", filename)

        with open(invoice_path, "wb") as f:
            f.write(invoice_file.read())

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO service_history
        (vehicle_id, service_date, km_done, hours_done,
         next_service_date, next_service_km, next_service_hours,
         cost, invoice_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vehicle_id,
        service_date,
        km_done,
        hours_done,
        next_service_date,
        next_service_km,
        next_service_hours,
        cost,
        invoice_path
    ))

    conn.commit()
    conn.close()


# ================= GET HISTORY =================
def get_service_history(vehicle_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    history = c.execute("""
        SELECT *
        FROM service_history
        WHERE vehicle_id = ?
        ORDER BY service_date DESC
    """, (vehicle_id,)).fetchall()

    conn.close()
    return history


# ================= DELETE SERVICE =================
def delete_service(service_id):
    conn = get_connection()
    c = conn.cursor()

    # Αν έχει τιμολόγιο, διαγράφουμε το αρχείο
    row = c.execute(
        "SELECT invoice_path FROM service_history WHERE id = ?",
        (service_id,)
    ).fetchone()

    if row and row[0]:
        if os.path.exists(row[0]):
            os.remove(row[0])

    c.execute("DELETE FROM service_history WHERE id = ?", (service_id,))
    conn.commit()
    conn.close()


# ================= TOTAL COST =================
def get_total_service_cost(vehicle_id):
    conn = get_connection()
    c = conn.cursor()

    total = c.execute("""
        SELECT SUM(cost)
        FROM service_history
        WHERE vehicle_id = ?
    """, (vehicle_id,)).fetchone()[0]

    conn.close()
    return total if total else 0
