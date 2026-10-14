import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rathinam.settings')
django.setup()

from transport_department.models import Institution, Vehicle, Student

def seed():
    insts = list(Institution.objects.all())
    if not insts:
        print("No institutions found!")
        return

    vehicles = list(Vehicle.objects.all())
    
    sample_students = [
        {
            "roll_number": "721721104001",
            "student_name": "Aakash V",
            "institution": insts[0],
            "academic_year": "2025-2026",
            "course": "B.Tech Artificial Intelligence & DS",
            "year_of_study": "3rd Year",
            "allocated_vehicle": vehicles[0] if vehicles else None,
            "route_name": "Route 1 - Gandhipuram Express",
            "pickup_point": "Gandhipuram Bus Stand",
            "drop_point": "Gandhipuram Bus Stand",
            "fee_demand": 24000.00,
            "fee_discount": 2000.00,
            "fee_paid": 22000.00,
            "contact_number": "9876543210",
            "parent_contact": "9876543211",
            "status": "Active"
        },
        {
            "roll_number": "721721104018",
            "student_name": "Deepika S",
            "institution": insts[0],
            "academic_year": "2025-2026",
            "course": "B.E Computer Science & Engg",
            "year_of_study": "4th Year",
            "allocated_vehicle": vehicles[0] if vehicles else None,
            "route_name": "Route 1 - Gandhipuram Express",
            "pickup_point": "Lakshmi Mills",
            "drop_point": "Lakshmi Mills",
            "fee_demand": 24000.00,
            "fee_discount": 0.00,
            "fee_paid": 24000.00,
            "contact_number": "9876543212",
            "parent_contact": "9876543213",
            "status": "Active"
        },
        {
            "roll_number": "721722104045",
            "student_name": "Kavitha R",
            "institution": insts[1] if len(insts) > 1 else insts[0],
            "academic_year": "2025-2026",
            "course": "B.Sc Computer Science",
            "year_of_study": "2nd Year",
            "allocated_vehicle": vehicles[1] if len(vehicles) > 1 else None,
            "route_name": "Route 3 - Pollachi Route",
            "pickup_point": "Pollachi New Bus Stand",
            "drop_point": "Pollachi New Bus Stand",
            "fee_demand": 28000.00,
            "fee_discount": 3000.00,
            "fee_paid": 15000.00,
            "contact_number": "9876543214",
            "parent_contact": "9876543215",
            "status": "Active"
        },
        {
            "roll_number": "721723104090",
            "student_name": "Mithun Kumar M",
            "institution": insts[1] if len(insts) > 1 else insts[0],
            "academic_year": "2025-2026",
            "course": "B.Com Information Technology",
            "year_of_study": "1st Year",
            "allocated_vehicle": vehicles[1] if len(vehicles) > 1 else None,
            "route_name": "Route 3 - Pollachi Route",
            "pickup_point": "Kinathukadavu Junction",
            "drop_point": "Kinathukadavu Junction",
            "fee_demand": 22000.00,
            "fee_discount": 0.00,
            "fee_paid": 10000.00,
            "contact_number": "9876543216",
            "parent_contact": "9876543217",
            "status": "Active"
        },
        {
            "roll_number": "721721104112",
            "student_name": "Naveen Raj P",
            "institution": insts[2] if len(insts) > 2 else insts[0],
            "academic_year": "2025-2026",
            "course": "Class XI - Bio-Maths",
            "year_of_study": "Schooling",
            "allocated_vehicle": vehicles[2] if len(vehicles) > 2 else None,
            "route_name": "Route 5 - RS Puram Route",
            "pickup_point": "RS Puram Head Post Office",
            "drop_point": "RS Puram Head Post Office",
            "fee_demand": 20000.00,
            "fee_discount": 0.00,
            "fee_paid": 20000.00,
            "contact_number": "9876543218",
            "parent_contact": "9876543219",
            "status": "Active"
        },
        {
            "roll_number": "721721104155",
            "student_name": "Sanjay Ganesh",
            "institution": insts[0],
            "academic_year": "2025-2026",
            "course": "MBA Logistics & SCM",
            "year_of_study": "PG / Masters",
            "allocated_vehicle": None,
            "route_name": "Pending Allocation",
            "pickup_point": "Sundarapuram",
            "drop_point": "Sundarapuram",
            "fee_demand": 18000.00,
            "fee_discount": 0.00,
            "fee_paid": 0.00,
            "contact_number": "9876543220",
            "parent_contact": "9876543221",
            "status": "Pending Allocation"
        }
    ]

    for s in sample_students:
        obj, created = Student.objects.update_or_create(
            roll_number=s["roll_number"],
            defaults=s
        )
        print(f"{'Created' if created else 'Updated'} student: {obj.student_name} ({obj.roll_number})")

if __name__ == '__main__':
    seed()
