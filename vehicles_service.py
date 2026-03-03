import sqlite3

DB_NAME = "fleet.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# ================= GET ALL =================
def get_all_vehicles():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    vehicles = c.execute("SELECT * FROM vehicles ORDER BY plate").fetchall()
    conn.close()
    return vehicles


# ================= ADD =================
def add_vehicle(
    plate, vtype, brand, model,
    current_km, current_hours,
    kteo_date, insurance_date,
    gas_card_date, tachograph_date   # 👈 ΠΡΟΣΘΗΚΗ
):

    conn = sqlite3.connect("fleet.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO vehicles
        (plate, type, brand, model,
         current_km, current_hours,
         kteo_date, insurance_date,
         gas_card_date, tachograph_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        plate, vtype, brand, model,
        current_km, current_hours,
        kteo_date, insurance_date,
        gas_card_date, tachograph_date
    ))

    conn.commit()
    conn.close()


# ================= UPDATE =================
def update_vehicle(
    vehicle_id,
    plate, vtype, brand, model,
    current_km, current_hours,
    kteo_date, insurance_date,
    gas_card_date, tachograph_date   # 👈 ΠΡΟΣΘΗΚΗ
):

    conn = sqlite3.connect("fleet.db")
    c = conn.cursor()

    c.execute("""
        UPDATE vehicles SET
            plate=?,
            type=?,
            brand=?,
            model=?,
            current_km=?,
            current_hours=?,
            kteo_date=?,
            insurance_date=?,
            gas_card_date=?,
            tachograph_date=?
        WHERE id=?
    """, (
        plate, vtype, brand, model,
        current_km, current_hours,
        kteo_date, insurance_date,
        gas_card_date, tachograph_date,
        vehicle_id
    ))

    conn.commit()
    conn.close()


# ================= DELETE =================
def delete_vehicle(vehicle_id):
    conn = get_connection()
    c = conn.cursor()

    # Διαγραφή service & damages πρώτα
    c.execute("DELETE FROM service_history WHERE vehicle_id = ?", (vehicle_id,))
    c.execute("DELETE FROM damages WHERE vehicle_id = ?", (vehicle_id,))
    c.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))

    conn.commit()
    conn.close()


# ================= UPDATE KM / HOURS =================
def update_vehicle_usage(vehicle_id, new_km, new_hours):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE vehicles
        SET current_km = ?,
            current_hours = ?
        WHERE id = ?
    """, (new_km, new_hours, vehicle_id))

    conn.commit()
    conn.close()
