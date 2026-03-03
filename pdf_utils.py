import sqlite3
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.platypus import TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

DB_NAME = "fleet.db"


def generate_vehicle_pdf(vehicle_id):

    os.makedirs("reports/vehicles", exist_ok=True)

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    vehicle = c.execute(
        "SELECT * FROM vehicles WHERE id = ?",
        (vehicle_id,)
    ).fetchone()

    services = c.execute(
        "SELECT * FROM service_history WHERE vehicle_id = ? ORDER BY service_date DESC",
        (vehicle_id,)
    ).fetchall()

    damages = c.execute(
        "SELECT * FROM damages WHERE vehicle_id = ? ORDER BY date DESC",
        (vehicle_id,)
    ).fetchall()

    conn.close()

    filename = f"reports/vehicles/{vehicle['plate']}_{vehicle['brand']}_{vehicle['model']}.pdf"

    # Unicode Font
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

    doc = SimpleDocTemplate(filename)
    elements = []

    styles = getSampleStyleSheet()
    greek_style = ParagraphStyle(
        name='Greek',
        parent=styles['Normal'],
        fontName='DejaVu',
        fontSize=11
    )

    title_style = ParagraphStyle(
        name='TitleGreek',
        parent=styles['Heading1'],
        fontName='DejaVu'
    )

    # ================= TITLE =================
    elements.append(Paragraph(
        f"Αναφορά Οχήματος: {vehicle['plate']} - {vehicle['brand']} {vehicle['model']}",
        title_style
    ))
    elements.append(Spacer(1, 0.3 * inch))

    # ================= VEHICLE INFO =================
    info_data = [
        ["Τύπος", vehicle["type"]],
        ["Τρέχοντα Χλμ", str(vehicle["current_km"])],
        ["Τρέχουσες Ώρες", str(vehicle["current_hours"])],
        ["ΚΤΕΟ", str(vehicle["kteo_date"])],
        ["Ασφάλεια", str(vehicle["insurance_date"])],
        ["Κάρτα Καυσαερίων", str(vehicle["gas_card_date"])]
    ]

    info_table = Table(info_data)
    info_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
]))

    elements.append(info_table)
    elements.append(Spacer(1, 0.5 * inch))

    # ================= SERVICE =================
    elements.append(Paragraph("Ιστορικό Service", title_style))
    elements.append(Spacer(1, 0.2 * inch))

    service_data = [["Ημερομηνία", "Χλμ", "Ώρες", "Κόστος"]]
    total_service_cost = 0

    for s in services:
        service_data.append([
            str(s["service_date"]),
            str(s["km_done"]),
            str(s["hours_done"]),
            f"{s['cost']} €"
        ])
        total_service_cost += s["cost"]

    service_data.append(["", "", "Σύνολο", f"{total_service_cost} €"])

    service_table = Table(service_data)
    service_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
]))

    elements.append(service_table)
    elements.append(Spacer(1, 0.5 * inch))

    # ================= DAMAGES =================
    elements.append(Paragraph("Ιστορικό Βλαβών", title_style))
    elements.append(Spacer(1, 0.2 * inch))

    damage_data = [["Ημερομηνία", "Περιγραφή", "Κατάσταση", "Κόστος"]]
    total_damage_cost = 0

    for d in damages:
        damage_data.append([
            str(d["date"]),
            str(d["description"]),
            str(d["status"]),
            f"{d['cost']} €"
        ])
        total_damage_cost += d["cost"]

    damage_data.append(["", "", "Σύνολο", f"{total_damage_cost} €"])

    damage_table = Table(damage_data)
    damage_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
]))

    elements.append(damage_table)
    elements.append(Spacer(1, 0.5 * inch))

    # ================= TOTAL =================
    grand_total = total_service_cost + total_damage_cost

    elements.append(Paragraph(
        f"Συνολικό Κόστος Οχήματος: {grand_total} €",
        title_style
    ))

    doc.build(elements)

    return filename
