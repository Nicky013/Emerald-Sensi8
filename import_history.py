"""
import_history.py — correct billing cycle version

BILLING CYCLE:
  Reading on 1st of month X = meter read on that date
  June bill = (Jul 1st reading) - (Jun 1st reading)
  May bill  = (Jun 1st reading) - (May 1st reading)
  Apr bill  = (May 1st reading) - (Apr 1st reading)

Column headers from Daniel's sheet (last 4 relevant columns):
  Apr 1st | May 1st | Jun 1st | Jul 1st
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'villas.db')

# Meter readings taken on the 1st of each month
READINGS = {
    #          Apr 1st   May 1st   Jun 1st   Jul 1st
    'S8-01':  [51989,    52923,    53718,    None],
    'S8-02':  [51660,    53650,    55802,    56772],
    'S8-03':  [79122,    81432,    83631,    85248],
    'S8-04':  [106064,   106850,   107160,   107439],
    'S8-05':  [42010,    43941,    45691,    47102],
    'S8-06':  [43158,    45199,    47253,    48582],
    'S8-07':  [41828,    43458,    44852,    46012],
    'S8-08':  [37377,    38776,    39624,    40471],
    'S8-09':  [28840,    29995,    31216,    31991],
    'S8-10':  [29624,    30713,    31431,    32150],
    'S8-11':  [12574,    13708,    14873,    15673],
    'S8-12':  [21562,    22339,    23297,    24088],
    'S8-13':  [7130,     7817,     9497,     10741],
    'SEV-01': [100117,   101457,   103125,   None],
    'SEV-02': [67654,    68436,    68784,    69417],
    'SEV-03': [94930,    96148,    96805,    97173],
    'SEV-04': [80528,    82169,    83659,    84968],
    'SEV-05': [70836,    72525,    72936,    73491],
    'SEV-06': [111306,   112603,   114023,   115340],
    'SEV-07': [81112,    82548,    83612,    84654],
    'SEV-08': [51039,    51330,    53061,    54820],
    'SEV-09': [130418,   131264,   132134,   134026],
    'SEV-10': [90150,    90852,    91855,    92708],
}

# Bill label, prev index (reading taken), curr index (reading taken)
# Apr bill = Apr 1st read -> May 1st read (invoice given in May)
# May bill = May 1st read -> Jun 1st read (invoice given in June)
# Jun bill = Jun 1st read -> Jul 1st read (invoice given in July)
BILLS = [
    ('April 2026', 0, 1, '01 Apr 2026', '01 May 2026'),
    ('May 2026',   1, 2, '01 May 2026', '01 Jun 2026'),
    ('June 2026',  2, 3, '01 Jun 2026', '01 Jul 2026'),
]

def next_invoice_no(c, project, billing_month):
    from datetime import datetime
    dt = datetime.strptime(billing_month, '%B %Y')
    prefix = 'S8' if 'Sense8' in project else 'SEV'
    pattern = f"{prefix}-ELEC-{dt.year}-{dt.month:02d}-%"
    c.execute('SELECT invoice_no FROM readings WHERE invoice_no LIKE ? ORDER BY invoice_no DESC LIMIT 1', (pattern,))
    row = c.fetchone()
    num = int(row[0].split('-')[-1]) + 1 if row else 1
    return f"{prefix}-ELEC-{dt.year}-{dt.month:02d}-{num:03d}"

def import_history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    total = 0
    skipped = 0

    for billing_month, prev_idx, curr_idx, prev_date, curr_date in BILLS:
        print(f"\n--- {billing_month} ---")
        for villa_id, reads in READINGS.items():
            prev = reads[prev_idx]
            curr = reads[curr_idx]
            if prev is None or curr is None:
                print(f"  SKIP {villa_id} — no July reading yet")
                skipped += 1
                continue

            villa = c.execute('SELECT * FROM villas WHERE id=?', (villa_id,)).fetchone()
            if not villa:
                continue

            units = curr - prev
            amount = round(units * villa['rate'], 2)
            inv_no = next_invoice_no(c, villa['project'], billing_month)

            c.execute('''INSERT INTO readings
                (villa_id, billing_month, previous_reading, previous_date,
                 current_reading, current_date, units, rate, amount,
                 invoice_no, invoice_date, due_date, status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (villa_id, billing_month, prev, prev_date,
                 curr, curr_date, units, villa['rate'], amount,
                 inv_no, curr_date, curr_date, 'Paid'))

            print(f"  {inv_no}  {villa_id}  {prev:,} → {curr:,}  ({units} units @ {villa['rate']})  {amount:,.2f} ฿")
            total += 1

    # Baselines for July billing — set current reading = Jul 1st read
    # So when Kun Sai enters August reading, previous auto-fills correctly
    print(f"\n--- July baselines (for next month entry) ---")
    for villa_id, reads in READINGS.items():
        jul = reads[3]
        jun = reads[2]
        baseline = jul if jul is not None else jun
        date = '01 Jul 2026' if jul is not None else '01 Jun 2026'
        villa = c.execute('SELECT rate FROM villas WHERE id=?', (villa_id,)).fetchone()
        c.execute('''INSERT INTO readings
            (villa_id, billing_month, current_reading, current_date, status)
            VALUES (?,?,?,?,?)''',
            (villa_id, '_baseline', baseline, date, 'Historical'))
        print(f"  {villa_id}: baseline {baseline:,} on {date}")

    conn.commit()
    conn.close()
    print(f"\nDone. {total} records imported, {skipped} skipped.")

if __name__ == '__main__':
    import_history()
