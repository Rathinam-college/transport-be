import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rathinam.settings')
django.setup()

from transport_department.models import TransportSummary

print("Seeding Full Operational + Expense Parameters into Django database...")

branches = ['RPS', 'KPM', 'College', 'Common']

months = [
    ('2025-09-01', 'Sep 1st to'),
    ('2025-10-01', 'Oct 1st to 31st'),
    ('2025-11-01', 'Nov 1st to'),
    ('2025-12-01', 'Dec 1st to'),
    ('2026-01-01', 'Jan 1st to 31st'),
    ('2026-02-01', 'Feb 1st to'),
    ('2026-03-01', 'Mar 1st to 31st'),
    ('2026-04-01', 'April 1st to'),
    ('2026-05-01', 'May 1st to'),
    ('2026-06-01', 'Jun 1st to'),
]

# Operational Matrix Data
matrix_raw_data = {
    '2025-09-01': {
        'RPS':     {'vehicles': 11, 'riders': 487, 'km_approved': 28691, 'km_actual': 25777, 'km_additional': 2481, 'statutory': 1, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'},
        'KPM':     {'vehicles': 5,  'riders': 270, 'km_approved': 7371,  'km_actual': 6500,  'km_additional': 894,  'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'College': {'vehicles': 31, 'riders': 1230,'km_approved': 85800, 'km_actual': 52335, 'km_additional': 2731, 'statutory': 2, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 1368, 'statutory': 1, 'incidents': 0, 'incident_link': ''},
    },
    '2025-10-01': {
        'RPS':     {'vehicles': 11, 'riders': 487, 'km_approved': 25420, 'km_actual': 23033, 'km_additional': 3515, 'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'KPM':     {'vehicles': 5,  'riders': 270, 'km_approved': 5460,  'km_actual': 5335,  'km_additional': 244,  'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'},
        'College': {'vehicles': 31, 'riders': 1230,'km_approved': 62920, 'km_actual': 49335, 'km_additional': 4171, 'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 450,  'statutory': 0, 'incidents': 0, 'incident_link': ''},
    },
    '2025-11-01': {
        'RPS':     {'vehicles': 11, 'riders': 487, 'km_approved': 33046, 'km_actual': 20032, 'km_additional': 5972, 'statutory': 1, 'incidents': 0, 'incident_link': ''},
        'KPM':     {'vehicles': 5,  'riders': 270, 'km_approved': 5733,  'km_actual': 5725,  'km_additional': 351,  'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'College': {'vehicles': 31, 'riders': 1230,'km_approved': 72358, 'km_actual': 65472, 'km_additional': 3291, 'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 190,  'statutory': 0, 'incidents': 0, 'incident_link': ''},
    },
    '2025-12-01': {
        'RPS':     {'vehicles': 11, 'riders': 487, 'km_approved': 27962, 'km_actual': 27270, 'km_additional': 7311, 'statutory': 2, 'incidents': 0, 'incident_link': ''},
        'KPM':     {'vehicles': 5,  'riders': 270, 'km_approved': 5460,  'km_actual': 5030,  'km_additional': 231,  'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'College': {'vehicles': 31, 'riders': 1230,'km_approved': 74658, 'km_actual': 66500, 'km_additional': 2573, 'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 0,    'statutory': 0, 'incidents': 0, 'incident_link': ''},
    },
    '2026-01-01': {
        'RPS':     {'vehicles': 11, 'riders': 487, 'km_approved': 21607, 'km_actual': 20400, 'km_additional': 3762, 'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'KPM':     {'vehicles': 5,  'riders': 270, 'km_approved': 4641,  'km_actual': 5175,  'km_additional': 281,  'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'College': {'vehicles': 31, 'riders': 1230,'km_approved': 53482, 'km_actual': 43204, 'km_additional': 2270, 'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 954,  'statutory': 0, 'incidents': 0, 'incident_link': ''},
    },
    '2026-02-01': {
        'RPS':     {'vehicles': 11, 'riders': 487, 'km_approved': 31775, 'km_actual': 29072, 'km_additional': 3894, 'statutory': 1, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - RPS.xlsx'},
        'KPM':     {'vehicles': 5,  'riders': 270, 'km_approved': 6006,  'km_actual': 6153,  'km_additional': 392,  'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'College': {'vehicles': 31, 'riders': 1230,'km_approved': 69212, 'km_actual': 60304, 'km_additional': 2827, 'statutory': 1, 'incidents': 0, 'incident_link': ''},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 0,    'statutory': 0, 'incidents': 0, 'incident_link': ''},
    },
    '2026-03-01': {
        'RPS':     {'vehicles': 11, 'riders': 487, 'km_approved': 28691, 'km_actual': 20000, 'km_additional': 4265, 'statutory': 3, 'incidents': 0, 'incident_link': ''},
        'KPM':     {'vehicles': 5,  'riders': 270, 'km_approved': 4368,  'km_actual': 4036,  'km_additional': 939,  'statutory': 1, 'incidents': 0, 'incident_link': ''},
        'College': {'vehicles': 31, 'riders': 1230,'km_approved': 77784, 'km_actual': 63534, 'km_additional': 2908, 'statutory': 2, 'incidents': 2, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 0,    'statutory': 1, 'incidents': 0, 'incident_link': ''},
    },
    '2026-04-01': {
        'RPS':     {'vehicles': 11, 'riders': 487, 'km_approved': 12710, 'km_actual': 6334,  'km_additional': 10084,'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'KPM':     {'vehicles': 5,  'riders': 270, 'km_approved': 4095,  'km_actual': 3200,  'km_additional': 70,   'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'College': {'vehicles': 31, 'riders': 1230,'km_approved': 55097, 'km_actual': 51503, 'km_additional': 1499, 'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 0,    'statutory': 0, 'incidents': 0, 'incident_link': ''},
    },
    '2026-05-01': {
        'RPS':     {'vehicles': 11, 'riders': 487, 'km_approved': 12710, 'km_actual': 352,   'km_additional': 4937, 'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'KPM':     {'vehicles': 5,  'riders': 270, 'km_approved': 0,     'km_actual': 125,   'km_additional': 0,    'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'College': {'vehicles': 31, 'riders': 1230,'km_approved': 55097, 'km_actual': 41022, 'km_additional': 1033, 'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 0,    'statutory': 0, 'incidents': 0, 'incident_link': ''},
    },
    '2026-06-01': {
        'RPS':     {'vehicles': 11, 'riders': 482, 'km_approved': 33046, 'km_actual': 21933, 'km_additional': 7918, 'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'KPM':     {'vehicles': 5,  'riders': 0,   'km_approved': 6006,  'km_actual': 5703,  'km_additional': 229,  'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'College': {'vehicles': 31, 'riders': 0,   'km_approved': 55097, 'km_actual': 42703, 'km_additional': 5624, 'statutory': 0, 'incidents': 0, 'incident_link': ''},
        'Common':  {'vehicles': 10, 'riders': 0,   'km_approved': 0,     'km_actual': 0,     'km_additional': 0,    'statutory': 0, 'incidents': 0, 'incident_link': ''},
    },
}

for m_str, branch_map in matrix_raw_data.items():
    m_date = datetime.datetime.strptime(m_str, '%Y-%m-%d').date()
    for b_name, data in branch_map.items():
        diesel = round(data['km_actual'] / 4.0, 2) if data['km_actual'] > 0 else 0
        fuel_cost = round(diesel * 92.5, 2)
        fc_cost = 15000.0 if (m_date.month == 4 and b_name in ['College', 'RPS']) else 0.0
        stat_cost = 8000.0 if m_date.month == 9 else 0.0
        repair_cost = round(35000.0 + (data['km_additional'] * 1.2), 2)
        others_cost = 12000.0
        emp_cost = round(data['vehicles'] * 18000.0, 2)
        cctv_cost = 4500.0 if m_date.month == 3 else 0.0
        parking_cost = 2500.0

        total_exp = round(fuel_cost + fc_cost + stat_cost + repair_cost + others_cost + emp_cost + cctv_cost + parking_cost, 2)

        TransportSummary.objects.update_or_create(
            branch=b_name,
            month=m_date,
            defaults={
                'vehicles': data['vehicles'],
                'riders': data['riders'],
                'km_approved': data['km_approved'],
                'km_actual': data['km_actual'],
                'km_additional': data['km_additional'],
                'statutory_compliance': data['statutory'],
                'incidents': data['incidents'],
                'diesel_litres': diesel,
                'fuel_expense': fuel_cost,
                'exp_fc': fc_cost,
                'exp_vehicle_statutory': stat_cost,
                'exp_repair': repair_cost,
                'exp_others': others_cost,
                'exp_employee_cost': emp_cost,
                'exp_cctv': cctv_cost,
                'exp_parking_fastag': parking_cost,
                'exp_total': total_exp,
                'source_ref': data['incident_link'] if data['incident_link'] else 'TRS-F-03'
            }
        )

print("Full Operational + Expense Matrix Data successfully seeded into Django database!")
