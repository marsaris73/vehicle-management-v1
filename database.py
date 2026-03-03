import sqlite3

DB_NAME = "fleet.db"

def init_db():

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ================= VEHICLES =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate TEXT,
        type TEXT,
        brand TEXT,
        model TEXT,
        current_km INTEGER,
        current_hours INTEGER,
        kteo_date TEXT,
        insurance_date TEXT,
        gas_card_date TEXT
    )
    """)

    # ================= SERVICE =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS service_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        service_date TEXT,
        km_done INTEGER,
        hours_done INTEGER,
        next_service_date TEXT,
        next_km INTEGER,
        next_hours INTEGER,
        cost REAL,
        invoice_path TEXT
    )
    """)

    # ================= DAMAGES =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS damages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        date TEXT,
        description TEXT,
        status TEXT,
        cost REAL
    )
    """)

    # ================= SETTINGS =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_email TEXT,
        sender_password TEXT,
        receiver_email TEXT
    )
    """)

    # ================= USERS =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # Default Admin
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute("""
            INSERT INTO users (username, password, role)
            VALUES ('admin', 'admin123', 'admin')
        """)

    # Προσθήκη πεδίου ταχογράφου αν δεν υπάρχει
    try:
        c.execute("ALTER TABLE vehicles ADD COLUMN tachograph_date TEXT")
    except:
        pass

    # ===== Ensure new columns exist =====
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

def add_column_if_not_exists(table, column_def):
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
    except:
        pass

add_column_if_not_exists("service_history", "next_service_km INTEGER")
add_column_if_not_exists("service_history", "next_service_hours INTEGER")

# Create default admin if none exists
conn = sqlite3.connect(DB_NAME)
conn.row_factory = sqlite3.Row
c = conn.cursor()

user = c.execute("SELECT * FROM users WHERE role='admin'").fetchone()

if not user:
    c.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
    """, ("admin", "1234", "admin"))

conn.commit()
conn.close()


