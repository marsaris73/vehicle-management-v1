import streamlit as st
import sqlite3
from database import init_db
from backup_utils import auto_backup
from dashboard_logic import get_dashboard_data
from vehicles_service import *
from service_service import *
from damages_service import *
from email_utils import send_notifications
from pdf_utils import generate_vehicle_pdf
from scheduler import send_daily_email_if_needed

init_db()

# =================================================
# LOGIN SYSTEM
# =================================================
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

if not st.session_state.user:

    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        conn = sqlite3.connect("fleet.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        user = c.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ?
        """, (username, password)).fetchone()

        conn.close()

        if user:
            st.session_state.user = user["username"]
            st.session_state.role = user["role"]
            st.rerun()
        else:
            st.error("Λάθος στοιχεία")

    st.stop()

# =================================================
# MAIN APP
# =================================================
send_daily_email_if_needed()

st.set_page_config(page_title="Vehicle Management Pro Version 1.0 by Bosswd", layout="wide")
st.title("🚛 Vehicle Management Pro")

role = st.session_state.role

# =================================================
# ROLE BASED MENU
# =================================================
menu_options = ["Dashboard"]

if role in ["admin", "user"]:
    menu_options += ["Service", "Βλάβες"]

if role == "admin":
    menu_options += ["Οχήματα", "PDF Αναφορά", "Ρυθμίσεις Email", "Οικονομικά", "Διαχείριση Χρηστών"]

menu = st.sidebar.selectbox("Μενού", menu_options)

# =================================================
# DASHBOARD
# =================================================
if menu == "Dashboard":

    data, warnings = get_dashboard_data()

    st.subheader("Κατάσταση Στόλου")

    for v in data:

        st.markdown(f"### {v['plate']} | {v['brand']} {v['model']}")

        # ================= ΕΓΓΡΑΦΑ =================
        if v.get("kteo_date"):
            st.write(f"📅 ΚΤΕΟ: {v['kteo_date']}")

        if v.get("insurance_date"):
            st.write(f"🛡 Ασφάλεια: {v['insurance_date']}")

        if v.get("gas_card_date"):
            st.write(f"🌫 Κάρτα Καυσαερίων: {v['gas_card_date']}")

        if v.get("tachograph_date"):
            st.write(f"🕓 Ταχογράφος: {v['tachograph_date']}")

        # ================= STATUS =================
        for s in v["status"]:
            st.write(s)

        # ================= SERVICE INFO =================
        if v.get("next_service_date"):
            st.write(f"🛠 Επόμενο Service (Ημερομηνία): {v['next_service_date']}")

        if v.get("next_service_km"):
            st.write(f"🚗 Επόμενο Service (Χλμ): {v['next_service_km']}")

        if v.get("next_service_hours"):
            st.write(f"⏱ Επόμενο Service (Ώρες): {v['next_service_hours']}")

        st.write(f"Σύνολο Service Κόστους: {v['total_service_cost']} €")

        st.markdown("---")

    if st.button("📧 Αποστολή Email Ειδοποιήσεων"):
        msg = send_notifications(warnings)
        st.info(msg)

# =================================================
# VEHICLES (ADMIN ONLY)
# =================================================
elif menu == "Οχήματα":

    st.subheader("➕ Προσθήκη / Επεξεργασία Οχήματος")

    if "edit_vehicle_id" not in st.session_state:
        st.session_state.edit_vehicle_id = None

    vehicles = get_all_vehicles()

    edit_vehicle = None
    if st.session_state.edit_vehicle_id:
        for v in vehicles:
            if v["id"] == st.session_state.edit_vehicle_id:
                edit_vehicle = v
                break

    def parse_date(value):
        if value:
            return datetime.strptime(value, "%Y-%m-%d").date()
        return None

    plate = st.text_input("Πινακίδα", value=edit_vehicle["plate"] if edit_vehicle else "")
    vtype = st.selectbox(
        "Τύπος",
        ["Φορτηγό", "ΙΧ", "Κλαρκ"],
        index=["Φορτηγό", "ΙΧ", "Κλαρκ"].index(edit_vehicle["type"]) if edit_vehicle else 0
    )
    brand = st.text_input("Μάρκα", value=edit_vehicle["brand"] if edit_vehicle else "")
    model = st.text_input("Μοντέλο", value=edit_vehicle["model"] if edit_vehicle else "")
    km = st.number_input("Τρέχοντα Χλμ", min_value=0, value=edit_vehicle["current_km"] if edit_vehicle else 0)
    hours = st.number_input("Τρέχουσες Ώρες", min_value=0, value=edit_vehicle["current_hours"] if edit_vehicle else 0)

    # ================= DOCUMENTS ONLY IF NOT KLARK =================
    if vtype != "Κλαρκ":

        kteo = st.date_input(
            "ΚΤΕΟ",
            value=parse_date(edit_vehicle["kteo_date"]) if edit_vehicle and edit_vehicle["kteo_date"] else None
        )

        insurance = st.date_input(
            "Ασφάλεια",
            value=parse_date(edit_vehicle["insurance_date"]) if edit_vehicle and edit_vehicle["insurance_date"] else None
        )

        gas = st.date_input(
            "Κάρτα Καυσαερίων",
            value=parse_date(edit_vehicle["gas_card_date"]) if edit_vehicle and edit_vehicle["gas_card_date"] else None
        )

        tachograph = st.date_input(
            "Ταχογράφος",
            value=parse_date(edit_vehicle["tachograph_date"]) if edit_vehicle and edit_vehicle["tachograph_date"] else None
        )

    else:
        kteo = None
        insurance = None
        gas = None
        tachograph = None

    # ================= SAVE =================
    if st.button("Αποθήκευση"):

        if edit_vehicle:
            update_vehicle(
                edit_vehicle["id"],
                plate, vtype, brand, model,
                km, hours,
                str(kteo) if kteo else None,
                str(insurance) if insurance else None,
                str(gas) if gas else None,
                str(tachograph) if tachograph else None
            )
            st.session_state.edit_vehicle_id = None
        else:
            add_vehicle(
                plate, vtype, brand, model,
                km, hours,
                str(kteo) if kteo else None,
                str(insurance) if insurance else None,
                str(gas) if gas else None,
                str(tachograph) if tachograph else None
            )

        auto_backup()
        st.rerun()

    st.markdown("---")
    st.subheader("📋 Λίστα Οχημάτων")

    for v in vehicles:

        col1, col2, col3 = st.columns([4, 1, 1])

        col1.write(f"{v['id']} - {v['plate']} | {v['brand']} {v['model']}")

        if col2.button("✏", key=f"edit{v['id']}"):
            st.session_state.edit_vehicle_id = v["id"]
            st.rerun()

        if role == "admin":
            if col3.button("❌", key=f"del{v['id']}"):
                delete_vehicle(v["id"])
                auto_backup()
                st.rerun()

# =================================================
# SERVICE
# =================================================
elif menu == "Service":

    vehicles = get_all_vehicles()

    if vehicles:
        vehicle_map = {
            f"{v['id']} - {v['plate']} | {v['brand']} {v['model']}": v["id"]
            for v in vehicles
        }

        selected = st.selectbox("Επιλογή Οχήματος", list(vehicle_map.keys()))
        vid = vehicle_map[selected]

        service_date = st.date_input("Ημερομηνία Service")
        next_date = st.date_input("Επόμενη Ημερομηνία")
        km_done = st.number_input("Χλμ Service", min_value=0)
        next_km = st.number_input("Επόμενα Χλμ", min_value=0)
        hours_done = st.number_input("Ώρες Service", min_value=0)
        next_hours = st.number_input("Επόμενες Ώρες", min_value=0)
        cost = st.number_input("Κόστος", min_value=0.0)
        invoice = st.file_uploader("Τιμολόγιο PDF", type=["pdf"])

        if st.button("Καταχώρηση Service"):
            add_service(
                vid,
                str(service_date),
                km_done,
                hours_done,
                str(next_date),
                next_km,
                next_hours,
                cost,
                invoice
            )
            auto_backup()
            st.rerun()

        st.markdown("---")
        history = get_service_history(vid)

        for h in history:
            st.write(f"{h['service_date']} | {h['cost']} €")

# =================================================
# DAMAGES
# =================================================
elif menu == "Βλάβες":

    vehicles = get_all_vehicles()

    if vehicles:
        vehicle_map = {
            f"{v['id']} - {v['plate']} | {v['brand']} {v['model']}": v["id"]
            for v in vehicles
        }

        selected = st.selectbox("Επιλογή Οχήματος", list(vehicle_map.keys()))
        vid = vehicle_map[selected]

        desc = st.text_area("Περιγραφή")
        cost = st.number_input("Κόστος Βλάβης", min_value=0.0)
        status = st.selectbox("Κατάσταση", ["Ανοιχτή", "Κλειστή"])

        if st.button("Καταχώρηση Βλάβης"):
            add_damage(vid, desc, cost, status)
            auto_backup()
            st.rerun()

        st.markdown("---")
        damages = get_damages(vehicle_id=vid)

        for d in damages:
            st.write(
                f"🚛 {selected} | {d['date']} | {d['description']} | {d['status']} | {d['cost']} €"
            )

# =================================================
# PDF
# =================================================
elif menu == "PDF Αναφορά":

    vehicles = get_all_vehicles()

    if vehicles:
        vehicle_map = {
            f"{v['id']} - {v['plate']} | {v['brand']} {v['model']}": v["id"]
            for v in vehicles
        }

        selected = st.selectbox("Επιλογή Οχήματος", list(vehicle_map.keys()))
        vid = vehicle_map[selected]

        if st.button("📄 Δημιουργία PDF"):
            path = generate_vehicle_pdf(vid)
            st.success(f"Δημιουργήθηκε: {path}")

# =================================================
# EMAIL SETTINGS (ADMIN ONLY)
# =================================================
elif menu == "Ρυθμίσεις Email":

    if role != "admin":
        st.warning("Δεν έχετε δικαίωμα πρόσβασης.")
        st.stop()

    st.subheader("📧 Ρυθμίσεις Email")

    conn = sqlite3.connect("fleet.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    existing = c.execute("SELECT * FROM settings LIMIT 1").fetchone()
    conn.close()

    sender = st.text_input("Email Αποστολέα", value=existing["sender_email"] if existing else "")
    password = st.text_input("App Password", value=existing["sender_password"] if existing else "", type="password")
    receiver = st.text_input("Email Παραλήπτη", value=existing["receiver_email"] if existing else "")

    if st.button("Αποθήκευση Ρυθμίσεων"):
        conn = sqlite3.connect("fleet.db")
        c = conn.cursor()
        c.execute("DELETE FROM settings")
        c.execute("""
            INSERT INTO settings (sender_email, sender_password, receiver_email)
            VALUES (?, ?, ?)
        """, (sender.strip(), password.strip(), receiver.strip()))
        conn.commit()
        conn.close()
        st.success("Αποθηκεύτηκε")

# =================================================
# FINANCIAL (ADMIN ONLY)
# =================================================
elif menu == "Οικονομικά":

    if role != "admin":
        st.warning("Δεν έχετε δικαίωμα πρόσβασης.")
        st.stop()

    from analytics import get_financial_overview
    import matplotlib.pyplot as plt
    import pandas as pd

    data = get_financial_overview()

    # ================= KPI =================
    col1, col2, col3 = st.columns(3)
    col1.metric("Σύνολο Service", f"{data['total_service']} €")
    col2.metric("Σύνολο Βλαβών", f"{data['total_damages']} €")
    col3.metric("Σύνολο Στόλου", f"{data['total_fleet']} €")

    st.markdown("---")

    # ================= COST PER VEHICLE =================
    st.subheader("Κόστος ανά Όχημα")

    if not data["merged_costs"].empty:

        merged = data["merged_costs"].merge(
            data["vehicles"],
            left_on="vehicle_id",
            right_on="id",
            how="left"
        )

        fig = plt.figure()
        plt.bar(merged["plate"], merged["total_cost"])
        plt.xticks(rotation=45)
        plt.title("Συνολικό Κόστος ανά Όχημα")
        st.pyplot(fig)

    # ================= MONTHLY SERVICE =================
    st.subheader("Μηνιαίο Κόστος Service")

    if not data["monthly_service"].empty:
        fig2 = plt.figure()
        plt.plot(data["monthly_service"]["month"], data["monthly_service"]["cost"])
        plt.xticks(rotation=45)
        plt.title("Service ανά Μήνα")
        st.pyplot(fig2)

    # ================= MONTHLY DAMAGE =================
    st.subheader("Μηνιαίο Κόστος Βλαβών")

    if not data["monthly_damage"].empty:
        fig3 = plt.figure()
        plt.plot(data["monthly_damage"]["month"], data["monthly_damage"]["cost"])
        plt.xticks(rotation=45)
        plt.title("Βλάβες ανά Μήνα")
        st.pyplot(fig3)

        # ================= EXPORT =================
    st.markdown("---")
    st.subheader("📥 Εξαγωγή Οικονομικής Αναφοράς")

    if not data["merged_costs"].empty:

        export_df = merged[["plate", "total_cost"]]

        import os
        from datetime import datetime

        os.makedirs("reports/financial", exist_ok=True)

        today_str = datetime.today().strftime("%Y-%m-%d")
        file_path = f"reports/financial/financial_report_{today_str}.xlsx"

        export_df.to_excel(file_path, index=False)

        st.success(f"Δημιουργήθηκε: {file_path}")

# =================================================
# USER MANAGEMENT (ADMIN ONLY)
# =================================================
elif menu == "Διαχείριση Χρηστών":

    if st.session_state.role != "admin":
        st.warning("Δεν έχετε δικαίωμα πρόσβασης.")
        st.stop()

    st.subheader("👥 Διαχείριση Χρηστών")

    import sqlite3
    conn = sqlite3.connect("fleet.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ================= ADD USER =================
    st.markdown("### ➕ Προσθήκη Χρήστη")

    new_username = st.text_input("Username")
    new_password = st.text_input("Password", type="password")
    new_role = st.selectbox("Ρόλος", ["user", "admin"])

    if st.button("Δημιουργία Χρήστη"):

        if new_username and new_password:

            existing = c.execute(
                "SELECT * FROM users WHERE username = ?",
                (new_username,)
            ).fetchone()

            if existing:
                st.error("Ο χρήστης υπάρχει ήδη.")
            else:
                c.execute("""
                    INSERT INTO users (username, password, role)
                    VALUES (?, ?, ?)
                """, (new_username.strip(), new_password.strip(), new_role))

                conn.commit()
                st.success("Ο χρήστης δημιουργήθηκε.")
                st.rerun()
        else:
            st.error("Συμπλήρωσε όλα τα πεδία.")

    st.markdown("---")

    # ================= LIST USERS =================
    st.markdown("### 📋 Λίστα Χρηστών")

    users = c.execute("SELECT * FROM users").fetchall()

    for u in users:

        col1, col2 = st.columns([4,1])

        col1.write(f"{u['username']} | Ρόλος: {u['role']}")

        if u["username"] != st.session_state.user:
            if col2.button("❌", key=f"del_user_{u['username']}"):
                c.execute("DELETE FROM users WHERE username = ?", (u["username"],))
                conn.commit()
                st.success("Διαγράφηκε.")
                st.rerun()

    conn.close()

from datetime import datetime

current_year = datetime.now().year

st.markdown("---")

st.markdown(
    f"""
    <div style="
        text-align:center;
        font-size:13px;
        color:#6c757d;
        padding-top:25px;
        padding-bottom:10px;
    ">
        <strong>Vehicle Management Pro</strong><br>
        Enterprise Vehicle Monitoring System<br><br>
        © {current_year} Bosswd by Aris | All Rights Reserved<br>
        Version 1.0 | Powered by Python & Streamlit
    </div>
    """,
    unsafe_allow_html=True
)