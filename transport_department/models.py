import os
from django.db import models
from django.conf import settings
from smart_selects.db_fields import ChainedForeignKey
from django.utils import timezone

def service_estimate_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        ext = '.pdf'
    if instance.request_id:
        new_filename = f"{instance.request_id}_estimate{ext}"
    else:
        new_filename = filename
    return os.path.join('service_estimates', new_filename)

def expense_bill_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        ext = '.pdf'
    
    sr_id = None
    if getattr(instance, 'service_request', None) and instance.service_request.request_id:
        sr_id = instance.service_request.request_id
    elif getattr(instance, 'service_request_id', None):
        try:
            from .models import ServiceRequest
            sr = ServiceRequest.objects.get(id=instance.service_request_id)
            if sr.request_id:
                sr_id = sr.request_id
        except Exception:
            pass

    if sr_id:
        new_filename = f"{sr_id}{ext}"
    else:
        new_filename = filename

    return os.path.join('bills', new_filename)
# Create your models here.
class Institution(models.Model):
    name = models.CharField(max_length=255)    
    address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='institutions_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='institutions_updated'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class RegisteredInstitution(models.Model):
    name = models.CharField(max_length=255, unique=True)
    
    # User Logging Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='registered_institutions_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='registered_institutions_updated'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=20, unique=True)
    cab_number = models.CharField(max_length=50, blank=True, null=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='vehicles')
    registered_institution = models.ForeignKey(RegisteredInstitution, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    
    # Detailed tracking fields
    seating_capacity = models.PositiveIntegerField(blank=True, null=True)
    make = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    chassis_number = models.CharField(max_length=100, blank=True, null=True)
    
    FUEL_CHOICES = (
        ('Petrol', 'Petrol'),
        ('Diesel', 'Diesel'),
        ('EV', 'EV'),
        ('CNG', 'CNG'),
    )
    fuel_type = models.CharField(max_length=10, choices=FUEL_CHOICES, blank=True, null=True)
    
    # Expiry and Renewal Dates moved to VehicleRenewal model
    
    # Operational Details
    driver_name = models.CharField(max_length=255, blank=True, null=True)
    driver_contact_no = models.CharField(max_length=20, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    
    remarks = models.TextField(blank=True, null=True)
    
    # Status Flags
    is_active = models.BooleanField(default=True, help_text="True if in working condition and running, false if under maintenance or not active")
    is_tracking = models.BooleanField(default=True, help_text="True if monitored with odometer and available on odometer entry/reports")
    
    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vehicle_number

class VehicleRenewal(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='renewals')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='renewals')
    
    DOCUMENT_CHOICES = (
        ('FC', 'FC'),
        ('Insurance', 'Insurance'),
        ('Road Tax', 'Road Tax'),
        ('Green Tax', 'Green Tax'),
        ('Permit', 'Permit'),
        ('PUCC', 'PUCC'),
        ('Kerala Permit', 'Kerala Permit'),
        ('Tiruppur Permit', 'Tiruppur Permit'),
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_CHOICES)
    document_number = models.CharField(max_length=100, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    new_expiry_date = models.DateField(blank=True, null=True)
    renewed_date = models.DateField(blank=True, null=True)
    
    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='renewals_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='renewals_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.document_type}"


class VehicleOperationalHistory(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='operational_history')
    effective_from = models.DateField(verbose_name="Effective From Date")
    effective_to = models.DateField(blank=True, null=True, verbose_name="Effective To Date")
    route_name = models.CharField(max_length=255, blank=True, null=True)
    actual_count = models.PositiveIntegerField(blank=True, null=True, help_text="How many are traveling")
    approved_kms = models.PositiveIntegerField(blank=True, null=True, verbose_name="Approved Km's")
    remarks = models.TextField(blank=True, null=True)
    
    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='operational_histories_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='operational_histories_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Vehicle Operational Histories"
        ordering = ['-effective_from', '-created_at']

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.route_name or 'Unassigned'} (from {self.effective_from})"

class VehicleMovement(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='movements')
    from_institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, related_name='movements_out')
    to_institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, related_name='movements_in')
    moved_at = models.DateTimeField(auto_now_add=True)
    moved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='movements_recorded')

    def __str__(self):
        return f"{self.vehicle.vehicle_number}: {self.from_institution} -> {self.to_institution}"


class FuelData(models.Model):    
    institution = models.CharField(max_length=255)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    date = models.DateField()
    previous_km = models.IntegerField(null=True, blank=True)
    current_km = models.IntegerField(null=True, blank=True)
    total_km = models.IntegerField(null=True, blank=True)
    bill_no = models.CharField(max_length=100, null=True, blank=True)
    is_direct_bill = models.BooleanField(default=False)
    liters = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='fuel_records_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='fuel_records_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Fuel Data"

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.date.strftime('%d-%m-%Y')} ({self.liters}L)"


class FuelRate(models.Model):
    FUEL_CHOICES = [
        ('PETROL', 'Petrol'),
        ('DIESEL', 'Diesel'),
        ('EV', 'EV'),
        ('CNG', 'CNG'),
    ]
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='DIESEL')
    rate_per_liter = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()
    effective_time = models.TimeField()
    
    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='fuel_rates_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='fuel_rates_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Fuel Rates"
        ordering = ['-effective_date', '-effective_time']

    def __str__(self):
        return f"{self.get_fuel_type_display()} @ ₹{self.rate_per_liter} from {self.effective_date} {self.effective_time.strftime('%H:%M')}"


class BudgetHead(models.Model):
    name = models.CharField(max_length=255, unique=True)
    institutions = models.ManyToManyField(Institution, blank=True, related_name='budget_heads')
    color_code = models.CharField(max_length=20, blank=True, null=True)
    
    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='budget_heads_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='budget_heads_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Budget Heads"

    def __str__(self):
        return self.name


class SubBudgetHead(models.Model):
    budget_head = models.ForeignKey(BudgetHead, on_delete=models.CASCADE, related_name='sub_heads')
    institutions = models.ManyToManyField(Institution, blank=True, related_name='sub_budget_heads')
    name = models.CharField(max_length=255)
    
    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_budget_heads_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_budget_heads_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Sub Budget Heads"
        unique_together = ('budget_head', 'name')

    def __str__(self):
        return f"{self.budget_head.name} - {self.name}"


class Vendor(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    
    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendors_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendors_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ServiceRequest(models.Model):
    request_id = models.CharField(max_length=20, unique=True, blank=True)
    date = models.DateField(default=timezone.now)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='service_requests')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='service_requests')
    kms_reading = models.PositiveIntegerField(blank=True, null=True)
    cab_no = models.CharField(max_length=50, blank=True, null=True)
    make = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    last_service_date = models.DateField(blank=True, null=True)
    nature_of_problem = models.TextField(blank=True, null=True)
    estimated_repair_cost = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vendor_name = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_requests')
    days_required = models.PositiveIntegerField(blank=True, null=True)
    expected_delivery_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    estimate_doc = models.FileField(upload_to=service_estimate_upload_path, blank=True, null=True, verbose_name="Estimate Document / PDF")
    
    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_requests_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_requests_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.request_id:
            date_str = timezone.now().strftime('%Y%m%d')
            prefix = f'SR{date_str}'
            last_request = ServiceRequest.objects.filter(request_id__startswith=prefix).order_by('-request_id').first()
            if last_request:
                last_number = int(last_request.request_id[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.request_id = f'{prefix}{new_number:04d}'

        if self.request_id and self.estimate_doc:
            ext = os.path.splitext(self.estimate_doc.name)[1].lower()
            if not ext:
                ext = '.pdf'
            desired_name = f"service_estimates/{self.request_id}_estimate{ext}"
            if self.estimate_doc.name != desired_name:
                self.estimate_doc.name = desired_name

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_id} - {self.vehicle.vehicle_number}"

class ExpenseRecord(models.Model):
    OPEX_CHOICES = [
        ('Settlement', 'Settlement'),
        ('Advance', 'Advance'),
    ]

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='expenses')
    vehicle = ChainedForeignKey(
        Vehicle,
        chained_field="institution",
        chained_model_field="institution",
        show_all=False,
        auto_choose=True,
        sort=True
    )
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='expense_records')
    date = models.DateField()
    
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    vendor_manual = models.CharField(max_length=255, blank=True, null=True, help_text="Fill if vendor not in list")
    
    budget_head = models.ForeignKey(BudgetHead, on_delete=models.CASCADE, related_name='expenses')
    sub_budget_head = ChainedForeignKey(
        SubBudgetHead,
        chained_field="budget_head",
        chained_model_field="budget_head",
        show_all=False,
        auto_choose=True,
        sort=True
    )
    
    purpose = models.TextField(blank=True, null=True)
    po_estimate_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="PO/Estimate No")
    po_estimate_date = models.DateField(blank=True, null=True, verbose_name="PO/Estimate Date")
    po_estimate_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="PO/Estimate Amount")
    
    service_km = models.PositiveIntegerField(blank=True, null=True, verbose_name="Service Km")
    bill_received_date = models.DateField(blank=True, null=True)
    bill_description = models.TextField(help_text="Detailed description of the bill")
    bill_no = models.CharField(max_length=100, blank=True, null=True)
    bill_date = models.DateField(blank=True, null=True)
    
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="SGST")
    cgst = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="CGST")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bill_file = models.FileField(upload_to=expense_bill_upload_path, blank=True, null=True, verbose_name="Bill PDF/File")
    remarks = models.TextField(blank=True, null=True)
    
    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Expense Record"
        verbose_name_plural = "Expense Records"

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.date.strftime('%d-%m-%Y')} ({self.total_amount})"
        
    def save(self, *args, **kwargs):
        # Auto-calculate total amount if not provided
        if not self.total_amount or self.total_amount == 0:
            self.total_amount = self.amount + self.sgst + self.cgst

        # If service_request is selected, rename uploaded bill_file to match Service Request request_id
        if self.service_request and self.service_request.request_id and self.bill_file:
            ext = os.path.splitext(self.bill_file.name)[1].lower()
            if not ext:
                ext = '.pdf'
            desired_basename = f"{self.service_request.request_id}{ext}"
            desired_name = f"bills/{desired_basename}"
            if self.bill_file.name != desired_name:
                self.bill_file.name = desired_name
        
        # Compress bill_file if exceeds 1MB
        if self.bill_file and hasattr(self.bill_file, 'file'):
            try:
                if self.bill_file.size > 1048576:
                    filename = os.path.basename(self.bill_file.name)
                    ext = os.path.splitext(filename)[1].lower()
                    if ext == '.pdf':
                        import pypdf, io
                        from django.core.files.base import ContentFile
                        reader = pypdf.PdfReader(self.bill_file.file)
                        writer = pypdf.PdfWriter()
                        for page in reader.pages:
                            page.compress_content_streams()
                            writer.add_page(page)
                        buffer = io.BytesIO()
                        writer.write(buffer)
                        buffer.seek(0)
                        if buffer.getbuffer().nbytes < self.bill_file.size:
                            self.bill_file.save(filename, ContentFile(buffer.getvalue()), save=False)
            except Exception as e:
                print("PDF Backend compression error:", e)

        super().save(*args, **kwargs)


class OpexDetail(models.Model):
    expense_record = models.ForeignKey(ExpenseRecord, on_delete=models.CASCADE, related_name='opex_details')
    opex_number = models.CharField(max_length=100, verbose_name="Opex Number")
    opex_date = models.DateField(verbose_name="Opex Date")
    opex_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Opex Amount")
    opex_type = models.CharField(max_length=20, choices=ExpenseRecord.OPEX_CHOICES, verbose_name="Opex Type")

    def __str__(self):
        return f"{self.opex_number} ({self.opex_date})"

class VehicleOdometerLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='odometer_logs')
    log_date = models.DateField()
    morning_930 = models.PositiveIntegerField(verbose_name="Morning 9:30 Reading")
    evening_330 = models.PositiveIntegerField(blank=True, null=True, verbose_name="Evening 3:30 Reading")
    remarks = models.TextField(blank=True, null=True)

    # User Logging Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='odometer_logs_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='odometer_logs_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Vehicle Odometer Logs"
        ordering = ['-log_date']
        unique_together = ('vehicle', 'log_date')

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.log_date}"


class TransportRemark(models.Model):
    BRANCH_CHOICES = (
        ('RPS', 'RPS'),
        ('KPM', 'KPM'),
        ('University', 'University'),
        ('College', 'University'),
        ('Common', 'Common'),
    )

    log_date = models.DateField()
    branch = models.CharField(max_length=20, blank=True, null=True, choices=BRANCH_CHOICES)
    title = models.CharField(max_length=255, default="Operational Activity")
    note = models.TextField()
    category = models.CharField(max_length=50, default="Incident", choices=(
        ('RTO Inspection', 'RTO Inspection'),
        ('Driver Safety', 'Driver Safety'),
        ('Incident', 'Incident'),
        ('Technology Rollout', 'Technology Rollout'),
        ('Audit', 'Audit'),
        ('Maintenance', 'Maintenance')
    ))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-log_date', '-created_at']

    def __str__(self):
        return f"{self.log_date} ({self.branch or 'General'}): {self.title}"


class Student(models.Model):
    RIDER_TYPE_CHOICES = (
        ('Student', 'Student'),
        ('Staff', 'Staff / Faculty'),
    )

    YEAR_CHOICES = (
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
        ('PG / Masters', 'PG / Masters'),
        ('Schooling', 'Schooling'),
        ('Faculty / Staff', 'Faculty / Staff'),
    )

    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Pass Surrendered', 'Pass Surrendered'),
        ('Suspended', 'Suspended'),
        ('Graduated', 'Graduated'),
        ('Pending Allocation', 'Pending Allocation'),
        ('Inactive', 'Inactive'),
    )

    rider_type = models.CharField(max_length=20, default="Student", choices=RIDER_TYPE_CHOICES, help_text="Passenger Type: Student or Staff / Faculty")
    roll_number = models.CharField(max_length=50, unique=True, help_text="Roll / Register / Staff ID / Admission Number")
    student_name = models.CharField(max_length=255, help_text="Student or Staff Full Name")
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='students')
    academic_year = models.CharField(max_length=20, default="2025-2026", help_text="e.g., 2025-2026, 2026-2027")
    course = models.CharField(max_length=150, blank=True, null=True, help_text="e.g., B.Tech CSE, MBA, Department of AI, Transport Admin")
    year_of_study = models.CharField(max_length=50, default="1st Year", choices=YEAR_CHOICES)
    
    # Transport Route & Vehicle Allocation
    allocated_vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='allocated_students',
        help_text="Assigned Bus or Cab"
    )
    route_name = models.CharField(max_length=150, blank=True, null=True, help_text="e.g. Route 12 - Gandhipuram Express")
    pickup_point = models.CharField(max_length=200, blank=True, null=True, help_text="Boarding stop")
    drop_point = models.CharField(max_length=200, blank=True, null=True, help_text="Return drop stop")
    
    # Fee Management
    fee_demand = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Annual Transport Fee")
    fee_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Concession / Discount")
    fee_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Amount Paid")
    
    # Pass Surrender & Discontinuation Tracking
    surrender_date = models.DateField(blank=True, null=True, help_text="Date when bus pass was surrendered / cancelled")
    surrender_reason = models.CharField(max_length=255, blank=True, null=True, help_text="Reason for surrendering/leaving bus pass")
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Refund amount issued if pass surrendered")
    remarks = models.TextField(blank=True, null=True, help_text="Additional surrender remarks or audit notes")
    
    # Contact Details
    contact_number = models.CharField(max_length=25, blank=True, null=True)
    parent_contact = models.CharField(max_length=25, blank=True, null=True)
    status = models.CharField(max_length=30, default="Active", choices=STATUS_CHOICES)
    
    # Audit Logging
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students_updated'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def fee_due(self):
        net_demand = max(0, float(self.fee_demand or 0) - float(self.fee_discount or 0))
        return max(0, net_demand - float(self.fee_paid or 0))

    class Meta:
        ordering = ['institution', 'student_name']
        verbose_name = "Student Transport Record"
        verbose_name_plural = "Student Transport Records"

    def __str__(self):
        return f"{self.roll_number} - {self.student_name} ({self.institution.name if self.institution else 'No Inst'})"

