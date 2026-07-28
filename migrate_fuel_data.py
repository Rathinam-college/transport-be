import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rathinam.settings')
django.setup()

from transport_department.models import FuelData, Institution

for f in FuelData.objects.all():
    if f.institution.isdigit():
        try:
            inst = Institution.objects.get(id=int(f.institution))
            f.institution = inst.name
            f.save(update_fields=['institution'])
            print(f'Updated {f.id} to {inst.name}')
        except Institution.DoesNotExist:
            print(f'Institution ID {f.institution} not found for FuelData {f.id}')
