import sqlite3
import pandas as pd

DB_NAME = "fleet.db"

def get_financial_overview():

    conn = sqlite3.connect(DB_NAME)

    vehicles = pd.read_sql("SELECT * FROM vehicles", conn)
    services = pd.read_sql("SELECT * FROM service_history", conn)
    damages = pd.read_sql("SELECT * FROM damages", conn)

    conn.close()

    # ================= TOTALS =================
    total_service = services["cost"].sum() if not services.empty else 0
    total_damages = damages["cost"].sum() if not damages.empty else 0
    total_fleet = total_service + total_damages

    # ================= MERGE ALL COSTS =================
    service_group = services.groupby("vehicle_id")["cost"].sum().reset_index() if not services.empty else pd.DataFrame(columns=["vehicle_id","cost"])
    damage_group = damages.groupby("vehicle_id")["cost"].sum().reset_index() if not damages.empty else pd.DataFrame(columns=["vehicle_id","cost"])

    merged = pd.merge(service_group, damage_group, on="vehicle_id", how="outer", suffixes=("_service","_damage")).fillna(0)
    merged["total_cost"] = merged["cost_service"] + merged["cost_damage"]

    # ================= MONTHLY =================
    if not services.empty:
        services["month"] = services["service_date"].str[:7]
        monthly_service = services.groupby("month")["cost"].sum().reset_index()
    else:
        monthly_service = pd.DataFrame(columns=["month","cost"])

    if not damages.empty:
        damages["month"] = damages["date"].str[:7]
        monthly_damage = damages.groupby("month")["cost"].sum().reset_index()
    else:
        monthly_damage = pd.DataFrame(columns=["month","cost"])

    return {
        "total_service": total_service,
        "total_damages": total_damages,
        "total_fleet": total_fleet,
        "vehicles": vehicles,
        "merged_costs": merged,
        "monthly_service": monthly_service,
        "monthly_damage": monthly_damage
    }
