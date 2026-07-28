import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rathinam.settings')
django.setup()

from transport_department.models import Vehicle, VehicleRenewal
from django.utils import timezone

def migrate_dates():
    vehicles = Vehicle.objects.all()
    count = 0
    for v in vehicles:
        dates_to_migrate = [
            ('FC', v.fc_expiry_date),
            ('Insurance', v.insurance_renewal_date),
            ('Road Tax', v.road_tax_date),
            ('Green Tax', v.green_tax_date),
            ('Permit', v.permit_date),
            ('PUCC', v.pucc_date),
            ('Kerala Permit', v.kerala_permit_date),
            ('Tiruppur Permit', v.tiruppur_permit_date),
        ]
        
        for doc_type, expiry_date in dates_to_migrate:
            if expiry_date:
                VehicleRenewal.objects.create(
                    institution=v.institution,
                    vehicle=v,
                    document_type=doc_type,
                    new_expiry_date=expiry_date,
                    # We don't know the exact renewed date, so we'll just set it to today or some default
                    renewed_date=timezone.now().date(),
                    amount_paid=0.00
                )
                count += 1
    
    print(f"Successfully migrated {count} renewal records.")

if __name__ == '__main__':
    migrate_dates()
