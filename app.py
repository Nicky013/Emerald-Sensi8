from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import sqlite3
import os
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'villas.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS villas (
        id TEXT PRIMARY KEY,
        project TEXT NOT NULL,
        villa_name TEXT NOT NULL,
        owner_name TEXT,
        occupant_name TEXT,
        occupancy_type TEXT,
        rate REAL NOT NULL,
        address TEXT,
        active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        villa_id TEXT NOT NULL,
        billing_month TEXT NOT NULL,
        previous_reading REAL,
        previous_date TEXT,
        current_reading REAL,
        current_date TEXT,
        units REAL,
        rate REAL,
        amount REAL,
        invoice_no TEXT,
        invoice_date TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'Unpaid',
        payment_method TEXT,
        date_paid TEXT,
        FOREIGN KEY (villa_id) REFERENCES villas(id)
    )''')

    conn.commit()

    # Seed villa data if empty
    c.execute('SELECT COUNT(*) FROM villas')
    if c.fetchone()[0] == 0:
        seed_villas(c)
        conn.commit()

    conn.close()

def seed_villas(c):
    villas = [
        # Sense8 Samui Villas
        ('S8-01','Sense8 Samui Villas','Sense8 Samui Villa 1','John & Lynne Lathbury','John & Lynne Lathbury','Owner Occupied',5.50,'Sense8 Samui Villa 1, 44/22 Moo5, Bophut, Koh Samui 84320'),
        ('S8-02','Sense8 Samui Villas','Sense8 Samui Villa 2','Erik Arnaes','','Short-Term Rental',7.00,'Sense8 Samui Villa 2, 44/23 Moo5, Bophut, Koh Samui 84320'),
        ('S8-03','Sense8 Samui Villas','Sense8 Samui Villa 3','James Bernesi','','Short-Term Rental',7.00,'Sense8 Samui Villa 3, 44/24 Moo5, Bophut, Koh Samui 84320'),
        ('S8-04','Sense8 Samui Villas','Sense8 Samui Villa 4','Patrick & Fiona Giorgi','Patrick & Fiona Giorgi','Owner Occupied',5.50,'Sense8 Samui Villa 4, 44/25 Moo5, Bophut, Koh Samui 84320'),
        ('S8-05','Sense8 Samui Villas','Sense8 Samui Villa 5','James Maughan','','Short-Term Rental',7.00,'Sense8 Samui Villa 5, 44/26 Moo5, Bophut, Koh Samui 84320'),
        ('S8-06','Sense8 Samui Villas','Sense8 Samui Villa 6','Camille Aymes','','Short-Term Rental',7.00,'Sense8 Samui Villa 6, 44/27 Moo5, Bophut, Koh Samui 84320'),
        ('S8-07','Sense8 Samui Villas','Sense8 Samui Villa 7','Lynne Lathbury','','Short-Term Rental',7.00,'Sense8 Samui Villa 7, 44/40 Moo5, Bophut, Koh Samui 84320'),
        ('S8-08','Sense8 Samui Villas','Sense8 Samui Villa 8','Cindy & Scott Myers','','Short-Term Rental',7.00,'Sense8 Samui Villa 8, 44/41 Moo5, Bophut, Koh Samui 84320'),
        ('S8-09','Sense8 Samui Villas','Sense8 Samui Villa 9','Frank Groeb','Frank Groeb','Owner Occupied',5.50,'Sense8 Samui Villa 9, 44/42 Moo5, Bophut, Koh Samui 84320'),
        ('S8-10','Sense8 Samui Villas','Sense8 Samui Villa 10','Katia Rizzello','Katia Rizzello','Owner Occupied',5.50,'Sense8 Samui Villa 10, 44/43 Moo5, Bophut, Koh Samui 84320'),
        ('S8-11','Sense8 Samui Villas','Sense8 Samui Villa 11','Erik Arnaes','','Short-Term Rental',7.00,'Sense8 Samui Villa 11, 44/44 Moo5, Bophut, Koh Samui 84320'),
        ('S8-12','Sense8 Samui Villas','Sense8 Samui Villa 12','Vladimir Deroberti','Vladimir Deroberti','Owner Occupied',5.50,'Sense8 Samui Villa 12, 44/45 Moo5, Bophut, Koh Samui 84320'),
        ('S8-13','Sense8 Samui Villas','Sense8 Samui Villa 13','John Muirhead','John Muirhead','Owner Occupied',5.50,'Sense8 Samui Villa 13, 44/46 Moo5, Bophut, Koh Samui 84320'),
        # Samui Emerald Villas
        ('SEV-01','Samui Emerald Villas','Samui Emerald Villa 1','James Bernesi','James Bernesi','Owner Occupied',5.76,'Samui Emerald Villa 1, 44/18 Moo5, Bophut, Koh Samui 84320'),
        ('SEV-02','Samui Emerald Villas','Samui Emerald Villa 2','Donna Benson & Neil Easton','Donna Benson & Neil Easton','Owner Occupied',5.76,'Samui Emerald Villa 2, 44/19 Moo5, Bophut, Koh Samui 84320'),
        ('SEV-03','Samui Emerald Villas','Samui Emerald Villa 3','John Muirhead','John Muirhead','Owner Occupied',5.76,'Samui Emerald Villa 3, 44/20 Moo5, Bophut, Koh Samui 84320'),
        ('SEV-04','Samui Emerald Villas','Samui Emerald Villa 4','Lawrence Lui','Ron Faigenbaum','Long-Term Tenant',6.00,'Samui Emerald Villa 4, 44/21 Moo5, Bophut, Koh Samui 84320'),
        ('SEV-05','Samui Emerald Villas','Samui Emerald Villa 5','Donna Benson & Neil Easton','Donna Benson & Neil Easton','Owner Occupied',5.76,'Samui Emerald Villa 5, 44/12 Moo5, Bophut, Koh Samui 84320'),
        ('SEV-06','Samui Emerald Villas','Samui Emerald Villa 6','Patrick & Fiona Giorgi','Aaron Dhwali','Long-Term Tenant',6.00,'Samui Emerald Villa 6, 44/13 Moo5, Bophut, Koh Samui 84320'),
        ('SEV-07','Samui Emerald Villas','Samui Emerald Villa 7','Simon Brown','Simon Brown','Owner Occupied',6.00,'Samui Emerald Villa 7, 44/14 Moo5, Bophut, Koh Samui 84320'),
        ('SEV-08','Samui Emerald Villas','Samui Emerald Villa 8','Robert Forstmeier','Robert Forstmeier','Owner Occupied',5.76,'Samui Emerald Villa 8, 44/15 Moo5, Bophut, Koh Samui 84320'),
        ('SEV-09','Samui Emerald Villas','Samui Emerald Villa 9','James Maughan','Shirly Ben Old','Long-Term Tenant',6.00,'Samui Emerald Villa 9, 44/16 Moo5, Bophut, Koh Samui 84320'),
        ('SEV-10','Samui Emerald Villas','Samui Emerald Villa 10','Ivor Roberts','Nicholas Kelly','Long-Term Tenant',6.00,'Samui Emerald Villa 10, 44/22 Moo5, Bophut, Koh Samui 84320'),
    ]
    c.executemany('INSERT INTO villas VALUES (?,?,?,?,?,?,?,?,1)', villas)


# ── Helpers ───────────────────────────────────────────────────────────────────

def next_invoice_no(project, billing_month, cursor=None):
    """Generate next invoice number e.g. S8-ELEC-2026-07-001"""
    dt = datetime.strptime(billing_month, '%B %Y')
    prefix = 'S8' if 'Sense8' in project else 'SEV'
    pattern = f"{prefix}-ELEC-{dt.year}-{dt.month:02d}-%"
    if cursor:
        cursor.execute('SELECT invoice_no FROM readings WHERE invoice_no LIKE ? ORDER BY invoice_no DESC LIMIT 1', (pattern,))
        row = cursor.fetchone()
    else:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT invoice_no FROM readings WHERE invoice_no LIKE ? ORDER BY invoice_no DESC LIMIT 1', (pattern,))
        row = c.fetchone()
        conn.close()
    if row:
        num = int(row[0].split('-')[-1]) + 1
    else:
        num = 1
    return f"{prefix}-ELEC-{dt.year}-{dt.month:02d}-{num:03d}"

def get_last_reading(villa_id, exclude_month=None):
    conn = get_db()
    c = conn.cursor()
    if exclude_month:
        c.execute('SELECT current_reading, current_date FROM readings WHERE villa_id=? AND billing_month!=? ORDER BY id DESC LIMIT 1', (villa_id, exclude_month))
    else:
        c.execute('SELECT current_reading, current_date FROM readings WHERE villa_id=? ORDER BY id DESC LIMIT 1', (villa_id,))
    row = c.fetchone()
    conn.close()
    return row

def fmt_thb(amount):
    return f"{amount:,.2f} THB"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT billing_month, 
                 SUM(amount) as total,
                 SUM(CASE WHEN status='Unpaid' THEN amount ELSE 0 END) as outstanding,
                 COUNT(*) as count
                 FROM readings WHERE invoice_no IS NOT NULL
                 GROUP BY billing_month ORDER BY id DESC LIMIT 12''')
    months = c.fetchall()

    c.execute('''SELECT v.project,
                 SUM(r.amount) as total,
                 SUM(CASE WHEN r.status='Unpaid' THEN r.amount ELSE 0 END) as outstanding
                 FROM readings r JOIN villas v ON r.villa_id = v.id
                 WHERE r.invoice_no IS NOT NULL
                 GROUP BY v.project''')
    by_project = c.fetchall()

    c.execute('''SELECT r.*, v.villa_name, v.project FROM readings r
                 JOIN villas v ON r.villa_id = v.id
                 WHERE r.invoice_no IS NOT NULL
                 ORDER BY r.id DESC LIMIT 20''')
    recent = c.fetchall()
    conn.close()
    return render_template('dashboard.html', months=months, by_project=by_project, recent=recent)


@app.route('/readings', methods=['GET', 'POST'])
def readings():
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        billing_month = request.form['billing_month']
        reading_date = request.form['reading_date']

        # Delete existing draft readings for this month (not yet invoiced)
        c.execute('DELETE FROM readings WHERE billing_month=? AND invoice_no IS NULL', (billing_month,))

        villas = c.execute('SELECT * FROM villas WHERE active=1 ORDER BY id').fetchall()
        for villa in villas:
            key = f"reading_{villa['id']}"
            val = request.form.get(key, '').strip()
            if not val:
                continue
            current = float(val)
            last = get_last_reading(villa['id'])
            prev_reading = last['current_reading'] if last else None
            prev_date = last['current_date'] if last else None
            units = round(current - prev_reading, 2) if prev_reading is not None else None
            amount = round(units * villa['rate'], 2) if units is not None else None
            c.execute('''INSERT INTO readings 
                (villa_id, billing_month, previous_reading, previous_date, current_reading, current_date, units, rate, amount)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (villa['id'], billing_month, prev_reading, prev_date, current, reading_date, units, villa['rate'], amount))

        conn.commit()
        conn.close()
        return redirect(url_for('readings') + f'?month={billing_month}')

    # GET — load villas and any existing readings for selected month
    selected_month = request.args.get('month', datetime.now().strftime('%B %Y'))
    villas = c.execute('SELECT * FROM villas WHERE active=1 ORDER BY id').fetchall()

    existing = {}
    rows = c.execute('SELECT * FROM readings WHERE billing_month=?', (selected_month,)).fetchall()
    for r in rows:
        existing[r['villa_id']] = r

    # Attach last reading to each villa
    villa_data = []
    for v in villas:
        last = get_last_reading(v['id'], exclude_month=selected_month)
        villa_data.append({
            'villa': v,
            'last_reading': last['current_reading'] if last else None,
            'last_date': last['current_date'] if last else None,
            'existing': existing.get(v['id'])
        })

    conn.close()
    today_str = date.today().strftime('%Y-%m-%d')
    return render_template('readings.html', villa_data=villa_data, selected_month=selected_month, today=today_str)


@app.route('/generate_invoices', methods=['POST'])
def generate_invoices():
    billing_month = request.form['billing_month']
    conn = get_db()
    c = conn.cursor()

    rows = c.execute('''SELECT r.*, v.project FROM readings r
                        JOIN villas v ON r.villa_id = v.id
                        WHERE r.billing_month=? AND r.invoice_no IS NULL AND r.amount IS NOT NULL''',
                     (billing_month,)).fetchall()

    today = date.today()
    invoice_date = today.strftime('%d %b %Y')
    due_date = today.replace(day=today.day + 7) if today.day <= 24 else today

    for row in rows:
        inv_no = next_invoice_no(row['project'], billing_month, cursor=c)
        c.execute('''UPDATE readings SET invoice_no=?, invoice_date=?, due_date=?, status='Unpaid'
                     WHERE id=?''',
                  (inv_no, invoice_date, due_date.strftime('%d %b %Y'), row['id']))
        conn.commit()

    
    conn.close()
    return redirect(url_for('invoices', month=billing_month))


@app.route('/invoices')
def invoices():
    conn = get_db()
    c = conn.cursor()
    month = request.args.get('month', datetime.now().strftime('%B %Y'))
    rows = c.execute('''SELECT r.*, v.villa_name, v.project, v.occupant_name, v.address, v.owner_name
                        FROM readings r JOIN villas v ON r.villa_id = v.id
                        WHERE r.billing_month=? AND r.invoice_no IS NOT NULL
                        ORDER BY r.invoice_no''', (month,)).fetchall()
    
    months = c.execute('SELECT DISTINCT billing_month FROM readings WHERE invoice_no IS NOT NULL ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('invoices.html', rows=rows, month=month, months=months, fmt_thb=fmt_thb)


@app.route('/invoice/<int:reading_id>/pdf')
def invoice_pdf(reading_id):
    conn = get_db()
    c = conn.cursor()
    row = c.execute('''SELECT r.*, v.villa_name, v.project, v.occupant_name, v.address, v.owner_name
                       FROM readings r JOIN villas v ON r.villa_id = v.id
                       WHERE r.id=?''', (reading_id,)).fetchone()
    conn.close()
    if not row:
        return 'Not found', 404
    pdf_bytes = generate_invoice_pdf(row)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f"{row['invoice_no']}.pdf")


@app.route('/invoices/batch_pdf')
def batch_pdf():
    month = request.args.get('month', datetime.now().strftime('%B %Y'))
    conn = get_db()
    c = conn.cursor()
    rows = c.execute('''SELECT r.*, v.villa_name, v.project, v.occupant_name, v.address, v.owner_name
                        FROM readings r JOIN villas v ON r.villa_id = v.id
                        WHERE r.billing_month=? AND r.invoice_no IS NOT NULL
                        ORDER BY r.invoice_no''', (month,)).fetchall()
    conn.close()

    from reportlab.platypus import PageBreak
    buffer = io.BytesIO()
    all_stories = []
    for i, row in enumerate(rows):
        story = build_invoice_story(row)
        all_stories.extend(story)
        if i < len(rows) - 1:
            all_stories.append(PageBreak())

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    doc.build(all_stories)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f"Invoices_{month.replace(' ','_')}.pdf")


@app.route('/invoice/<int:reading_id>/mark_paid', methods=['POST'])
def mark_paid(reading_id):
    method = request.form.get('method', 'Cash')
    conn = get_db()
    conn.execute('''UPDATE readings SET status='Paid', payment_method=?, date_paid=?
                    WHERE id=?''', (method, date.today().strftime('%d %b %Y'), reading_id))
    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('invoices'))


@app.route('/villas')
def villa_register():
    conn = get_db()
    villas = conn.execute('SELECT * FROM villas ORDER BY id').fetchall()
    conn.close()
    return render_template('villas.html', villas=villas)


@app.route('/villa/<villa_id>/edit', methods=['GET', 'POST'])
def edit_villa(villa_id):
    conn = get_db()
    if request.method == 'POST':
        conn.execute('''UPDATE villas SET occupant_name=?, occupancy_type=?, rate=? WHERE id=?''',
                     (request.form['occupant_name'], request.form['occupancy_type'],
                      float(request.form['rate']), villa_id))
        conn.commit()
        conn.close()
        return redirect(url_for('villa_register'))
    villa = conn.execute('SELECT * FROM villas WHERE id=?', (villa_id,)).fetchone()
    conn.close()
    return render_template('edit_villa.html', villa=villa)


# ── PDF Generation ────────────────────────────────────────────────────────────

def build_invoice_story(row):
    styles = getSampleStyleSheet()
    project = row['project']
    address_line = '44/25 Moo 5 Bophut, Koh Samui Surat Thani 84320' if 'Sense8' in project else '44/16 Moo 5 Bophut, Koh Samui Surat Thani 84320'
    accent = colors.HexColor('#1B4F72')

    title_style = ParagraphStyle('Title', fontSize=16, textColor=accent, spaceAfter=2, fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('Sub', fontSize=9, textColor=colors.HexColor('#555555'), spaceAfter=1)
    label_style = ParagraphStyle('Label', fontSize=8, textColor=colors.grey, fontName='Helvetica-Bold')
    value_style = ParagraphStyle('Value', fontSize=10, fontName='Helvetica')
    small_style = ParagraphStyle('Small', fontSize=8, textColor=colors.HexColor('#444444'))
    total_style = ParagraphStyle('Total', fontSize=14, fontName='Helvetica-Bold', textColor=accent, alignment=TA_RIGHT)

    occupant = row['occupant_name'] or row['owner_name'] or ''
    prev = f"{float(row['previous_reading']):,.0f}" if row['previous_reading'] is not None else '-'
    curr = f"{float(row['current_reading']):,.0f}" if row['current_reading'] is not None else '-'
    units = f"{float(row['units']):,.0f}" if row['units'] is not None else '-'
    rate = f"{float(row['rate']):.2f}"
    amount = fmt_thb(float(row['amount'])) if row['amount'] else '-'
    billing_period = f"{row['previous_date']} – {row['current_date']}" if row['previous_date'] else f"– {row['current_date']}"

    story = [
        Paragraph(project, title_style),
        Paragraph(address_line, sub_style),
        HRFlowable(width='100%', thickness=1, color=accent, spaceAfter=8),
        Paragraph('ELECTRICITY INVOICE', ParagraphStyle('H', fontSize=13, fontName='Helvetica-Bold', spaceAfter=8)),
    ]

    # Header info table
    header_data = [
        [Paragraph('Invoice No.', label_style), Paragraph(row['invoice_no'] or '', value_style),
         Paragraph('Invoice Date', label_style), Paragraph(row['invoice_date'] or '', value_style)],
        [Paragraph('Billing Period', label_style), Paragraph(billing_period, value_style),
         Paragraph('Due Date', label_style), Paragraph(row['due_date'] or '', value_style)],
        [Paragraph('Villa', label_style), Paragraph(row['villa_name'], value_style),
         Paragraph('Occupant', label_style), Paragraph(occupant, value_style)],
    ]
    ht = Table(header_data, colWidths=[35*mm, 65*mm, 35*mm, 35*mm])
    ht.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(ht)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Property Address', label_style))
    story.append(Paragraph(row['address'] or '', small_style))
    story.append(Spacer(1, 6*mm))

    # Meter readings table
    story.append(Paragraph('Meter Reading Details', ParagraphStyle('MH', fontSize=10, fontName='Helvetica-Bold', spaceAfter=4)))
    meter_data = [
        ['Previous', 'Date', 'Current', 'Date', 'Units', 'Rate (THB)', 'Total'],
        [prev, row['previous_date'] or '-', curr, row['current_date'] or '-', units, rate, amount]
    ]
    mt = Table(meter_data, colWidths=[25*mm, 28*mm, 25*mm, 28*mm, 18*mm, 22*mm, 24*mm])
    mt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), accent),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F0F4F8'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(mt)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(f'TOTAL DUE: {amount}', total_style))
    story.append(Paragraph(f'Payment due: {row["due_date"] or ""}',
                           ParagraphStyle('Due', fontSize=9, textColor=colors.HexColor('#E74C3C'), alignment=TA_RIGHT)))
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#CCCCCC'), spaceAfter=6))

    # Payment options
    story.append(Paragraph('Payment Options', ParagraphStyle('PH', fontSize=10, fontName='Helvetica-Bold', spaceAfter=4)))
    pay_data = [
        ['Bank Transfer', 'Krungsri Bank'],
        ['Account Name', 'Sense8 Samui Villas Co Ltd'],
        ['Account Number', '6211169765'],
        ['Alternative', 'Cash at management office / PayPal / Airbnb where applicable'],
    ]
    pt = Table(pay_data, colWidths=[40*mm, 130*mm])
    pt.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),  # Hmm just col 0
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#555555')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(pt)
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph('Thank you for your prompt payment.',
                           ParagraphStyle('Thanks', fontSize=9, textColor=colors.HexColor('#27AE60'), fontName='Helvetica-Bold')))
    return story


def generate_invoice_pdf(row):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    doc.build(build_invoice_story(row))
    buffer.seek(0)
    return buffer.read()


# ── Run ───────────────────────────────────────────────────────────────────────

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
