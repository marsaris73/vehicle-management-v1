import sqlite3
from datetime import datetime

DB_NAME = "fleet.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# ================= ADD DAMAGE =================
def add_damage(vehicle_id, description, cost, status="Ανοιχτή"):

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO damages
        (vehicle_id, date, description, cost, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        vehicle_id,
        datetime.now().strftime("%Y-%m-%d"),
        description,
        cost,
        status
    ))

    conn.commit()
    conn.close()


# ================= GET DAMAGES =================
def get_damages(vehicle_id=None, status_filter=None):

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM damages"
    params = []

    conditions = []

    if vehicle_id:
        conditions.append("vehicle_id = ?")
        params.append(vehicle_id)

    if status_filter:
        conditions.append("status = ?")
        params.append(status_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY date DESC"

    damages = c.execute(query, params).fetchall()

    conn.close()
    return damages


# ================= UPDATE DAMAGE STATUS =================
def update_damage_status(damage_id, new_status):

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE damages
        SET status = ?
        WHERE id = ?
    """, (new_status, damage_id))

    conn.commit()
    conn.close()


# ================= DELETE DAMAGE =================
def delete_damage(damage_id):

    conn = get_connection()
    c = conn.cursor()

    c.execute("DELETE FROM damages WHERE id = ?", (damage_id,))
    conn.commit()
    conn.close()


# ================= TOTAL COST =================
def get_total_damage_cost(vehicle_id=None):

    conn = get_connection()
    c = conn.cursor()

    if vehicle_id:
        total = c.execute("""
            SELECT SUM(cost)
            FROM damages
            WHERE vehicle_id = ?
        """, (vehicle_id,)).fetchone()[0]
    else:
        total = c.execute("""
            SELECT SUM(cost)
            FROM damages
        """).fetchone()[0]

    conn.close()
    return total if total else 0
