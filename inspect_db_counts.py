import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rathinam.settings')
django.setup()

from transport_department.models import (
    Institution, RegisteredInstitution, Vehicle, VehicleMovement,
    FuelData, FuelRate, BudgetHead, SubBudgetHead, Vendor,
    ExpenseRecord, OpexDetail, ServiceRequest, VehicleOperationalHistory,
    VehicleRenewal, VehicleOdometerLog, TransportRemark
)

models = [
    ("Institutions", Institution),
    ("Registered Institutions", RegisteredInstitution),
    ("Vehicles", Vehicle),
    ("Movements", VehicleMovement),
    ("Fuel Records", FuelData),
    ("Fuel Rates", FuelRate),
    ("Budget Heads", BudgetHead),
    ("Sub Budget Heads", SubBudgetHead),
    ("Vendors", Vendor),
    ("Expense Records", ExpenseRecord),
    ("Opex Details", OpexDetail),
    ("Service Requests", ServiceRequest),
    ("Vehicle Operational History", VehicleOperationalHistory),
    ("Vehicle Renewals", VehicleRenewal),
    ("Vehicle Odometer Logs", VehicleOdometerLog),
    ("Transport Remarks", TransportRemark),
]

print("=== POSTGRESQL DATABASE RECORD COUNTS ===")
for name, model in models:
    count = model.objects.count()
    print(f"{name:<30}: {count} records")
