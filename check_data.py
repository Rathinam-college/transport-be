import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rathinam.settings')
django.setup()

from transport_department.models import ServiceRequest, ExpenseRecord, OpexDetail

print("--- Service Requests & Expenses ---")
for sr in ServiceRequest.objects.all():
    expenses = ExpenseRecord.objects.filter(service_request=sr)
    for expense in expenses:
        print(f"SR ID: {sr.id} | Request ID: {sr.request_id} | Est Repair Cost (Advance from SR?): {sr.estimated_repair_cost}")
        print(f"  Expense ID: {expense.id} | Total Amount (Actual): {expense.total_amount}")
        advances = OpexDetail.objects.filter(expense_record=expense, opex_type='Advance')
        total_advance = sum(adv.opex_amount for adv in advances)
        print(f"  Total Advance Given (from Opex): {total_advance}")
        print("-" * 40)
