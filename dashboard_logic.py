import sqlite3
from datetime import datetime, date

DB_NAME = "fleet.db"

WARNING_DAYS = 15
WARNING_KM = 1000
WARNING_HOURS = 50


def get_dashboard_data():

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    vehicles = c.execute("SELECT * FROM vehicles").fetchall()
    services = c.execute("SELECT * FROM service_history").fetchall()

    conn.close()

    today = date.today()

    results = []
    email_warnings = []

    for v in vehicles:

        vehicle_services = [s for s in services if s["vehicle_id"] == v["id"]]

        status_list = []
        total_service_cost = sum([s["cost"] for s in vehicle_services])

        # ================= DATE CHECKS =================
        for field, label in [
            ("kteo_date", "ΚΤΕΟ"),
            ("insurance_date", "Ασφάλεια"),
            ("gas_card_date", "Κάρτα Καυσαερίων"),
            ("tachograph_date", "Ταχογράφος")   # ✅ ΝΕΟ
        ]:
            value = v[field] if field in v.keys() else None

            if value:
                expiry = datetime.strptime(value, "%Y-%m-%d").date()
                days_left = (expiry - today).days

                if days_left < 0:
                    msg = f"🔴 Εκπρόθεσμο {label}"
                    status_list.append(msg)
                    email_warnings.append(f"{v['plate']} - {msg}")

                elif days_left <= WARNING_DAYS:
                    msg = f"🟠 Προειδοποίηση {label}"
                    status_list.append(msg)
                    email_warnings.append(f"{v['plate']} - {msg}")

                # ================= SERVICE CHECK (DATE ONLY) =================
        if vehicle_services:
            last = vehicle_services[-1]

            if last["next_service_date"]:
                next_date = datetime.strptime(last["next_service_date"], "%Y-%m-%d").date()
                days_left = (next_date - today).days

                if days_left < 0:
                    msg = "🔴 Εκπρόθεσμο Service"
                    status_list.append(msg)
                    email_warnings.append(f"{v['plate']} - {msg}")

                elif days_left <= WARNING_DAYS:
                    msg = "🟠 Προειδοποίηση Service"
                    status_list.append(msg)
                    email_warnings.append(f"{v['plate']} - {msg}")

           # ================= LAST SERVICE INFO =================
        next_service_date = None
        next_service_km = None
        next_service_hours = None

        if vehicle_services:
            last = vehicle_services[-1]
            next_service_date = last["next_service_date"]
            next_service_km = last["next_service_km"]
            next_service_hours = last["next_service_hours"]

        results.append({
            "id": v["id"],
            "plate": v["plate"],
            "brand": v["brand"],
            "model": v["model"],
            "type": v["type"],
            "kteo_date": v["kteo_date"],
            "insurance_date": v["insurance_date"],
            "gas_card_date": v["gas_card_date"],
            "tachograph_date": v["tachograph_date"],
            "status": status_list if status_list else ["🟢 OK"],
            "total_service_cost": total_service_cost,
            "next_service_date": next_service_date,
            "next_service_km": next_service_km,
            "next_service_hours": next_service_hours
        })

    return results, email_warnings