from django.db import models
from django.conf import settings
from smart_selects.db_fields import ChainedForeignKey
from django.utils import timezone
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
    estimate_doc = models.FileField(upload_to='service_estimates/', blank=True, null=True, verbose_name="Estimate Document / PDF")
    
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
    bill_file = models.FileField(upload_to='bills/', blank=True, null=True, verbose_name="Bill PDF/File")
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


class TransportSummary(models.Model):
    BRANCH_CHOICES = (
        ('RPS', 'RPS'),
        ('KPM', 'KPM'),
        ('College', 'College'),
        ('Common', 'Common'),
    )

    branch = models.CharField(max_length=20, choices=BRANCH_CHOICES)
    month = models.DateField(help_text="First day of the month, e.g., 2025-09-01")
    
    # Fleet & Ridership
    vehicles = models.PositiveIntegerField(default=0)
    riders = models.PositiveIntegerField(default=0)

    # Distance Tracking
    km_approved = models.PositiveIntegerField(default=0)
    km_actual = models.PositiveIntegerField(default=0)
    km_additional = models.PositiveIntegerField(default=0)

    # Compliance & Safety
    statutory_compliance = models.PositiveIntegerField(default=0)
    incidents = models.PositiveIntegerField(default=0)

    # Service Desk
    tickets_raised = models.PositiveIntegerField(default=0)
    tickets_closed = models.PositiveIntegerField(default=0)
    tickets_open = models.PositiveIntegerField(default=0)

    # Quality Desk
    quality_received = models.PositiveIntegerField(default=0)
    quality_closed = models.PositiveIntegerField(default=0)
    quality_open = models.PositiveIntegerField(default=0)

    # Fuel Metrics
    diesel_litres = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fuel_expense = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Expense Breakdown
    exp_fc = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    exp_vehicle_statutory = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    exp_repair = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    exp_others = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    exp_employee_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    exp_cctv = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    exp_parking_fastag = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    exp_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Budget Metrics
    budget_approved = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_spent_cumulative = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Fee Collection
    fee_demand = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fee_discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fee_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fee_unpaid = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Unit Economics & Feedback
    cost_per_student = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fee_per_student_year = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    feedback_score = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    cab_request_billing = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Reference Tracker File Name
    source_ref = models.CharField(max_length=255, blank=True, null=True, default="odometer_tracker_2025-26.xlsx")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Transport Summaries"
        unique_together = ('branch', 'month')
        ordering = ['-month', 'branch']

    def __str__(self):
        return f"{self.branch} - {self.month.strftime('%Y-%m')}"


class TransportRemark(models.Model):
    log_date = models.DateField()
    branch = models.CharField(max_length=20, blank=True, null=True, choices=TransportSummary.BRANCH_CHOICES)
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
