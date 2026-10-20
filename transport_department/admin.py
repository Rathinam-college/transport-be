from django.contrib import admin
from django.contrib.admin.models import LogEntry
from .models import (Institution, RegisteredInstitution, Vehicle, VehicleRenewal, VehicleMovement, FuelData, 
                     BudgetHead, SubBudgetHead, Vendor, ExpenseRecord, OpexDetail, ServiceRequest, Student)

from rangefilter.filters import DateRangeFilter
from django import forms


# Admin Site Branding
admin.site.site_header = "Rathinam Transport Department"
admin.site.site_title = "Rathinam Admin"
admin.site.index_title = "Welcome to Rathinam Transport Department"


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag')
    list_filter = ('user', 'content_type', 'action_flag')
    search_fields = ('object_repr', 'change_message')
    date_hierarchy = 'action_time'

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


# Register your models here.
@admin.register(RegisteredInstitution)
class RegisteredInstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'updated_by', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'created_by', 'updated_by', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'cab_number', 'make', 'model', 'institution', 'registered_institution')
    list_filter = ('institution', 'registered_institution')
    search_fields = ('vehicle_number', 'cab_number', 'make', 'model', 'chassis_number')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('vehicle_number', 'cab_number', 'institution', 'registered_institution', 'route_name', 'actual_count')
        }),
        ('Vehicle Details', {
            'fields': ('make', 'model', 'chassis_number', 'seating_capacity')
        }),
        ('Operational Details', {
            'fields': ('driver_name', 'driver_contact_no', 'approved_kms', 'purpose')
        }),
        ('Other Details', {
            'fields': ('remarks',)
        }),
        ('Audit Log', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if change: # If updating an existing vehicle
            old_obj = Vehicle.objects.get(pk=obj.pk)
            if old_obj.institution != obj.institution:
                # Track the movement
                VehicleMovement.objects.create(
                    vehicle=obj,
                    from_institution=old_obj.institution,
                    to_institution=obj.institution,
                    moved_by=request.user
                )
        
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(VehicleMovement)
class VehicleMovementAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'from_institution', 'to_institution', 'moved_at', 'moved_by')
    readonly_fields = ('vehicle', 'from_institution', 'to_institution', 'moved_at', 'moved_by')
    
    # Disable adding/editing movements manually to keep logs accurate
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False


@admin.register(FuelData)
class FuelDataAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'institution', 'formatted_date', 'liters', 'amount', 'created_by')
    list_filter = ('institution', ('date', DateRangeFilter))
    search_fields = ('vehicle__vehicle_number', 'institution__name')
    
    def formatted_date(self, obj):
        return obj.date.strftime('%d-%m-%Y')
    formatted_date.short_description = 'Date'
    formatted_date.admin_order_field = 'date'
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['date'].input_formats = ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']
        form.base_fields['date'].widget.format = '%d-%m-%Y'
        return form

    list_per_page = 15 

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BudgetHead)
class BudgetHeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SubBudgetHead)
class SubBudgetHeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget_head', 'created_by', 'updated_at')
    list_filter = ('budget_head',)
    search_fields = ('name', 'budget_head__name')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'email', 'updated_at')
    search_fields = ('name', 'contact_number', 'email', 'gst_number')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'vehicle', 'institution', 'date', 'estimated_repair_cost', 'vendor_name', 'expected_delivery_date')
    list_filter = ('institution', 'vendor_name', ('date', DateRangeFilter))
    search_fields = ('request_id', 'vehicle__vehicle_number', 'nature_of_problem', 'remarks')
    readonly_fields = ('request_id', 'created_by', 'updated_by', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class OpexDetailInline(admin.TabularInline):
    model = OpexDetail
    extra = 1
    fields = ('opex_number', 'opex_type', 'opex_date', 'opex_amount')

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Apply date format to inline date field
        form = formset.form
        if 'opex_date' in form.base_fields:
            form.base_fields['opex_date'].input_formats = ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']
            form.base_fields['opex_date'].widget.format = '%d-%m-%Y'
        return formset


@admin.register(ExpenseRecord)
class ExpenseRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'formatted_date', 'budget_head', 'get_opex_numbers', 'total_amount', 'updated_at')
    list_filter = ('institution', 'budget_head', ('date', DateRangeFilter))
    search_fields = ('vehicle__vehicle_number', 'bill_no', 'po_estimate_no', 'opex_details__opex_number', 'vendor_manual', 'vendor__name')
    readonly_fields = ('total_amount', 'created_by', 'updated_by', 'created_at', 'updated_at')
    inlines = [OpexDetailInline]

    def formatted_date(self, obj):
        return obj.date.strftime('%d-%m-%Y')
    formatted_date.short_description = 'Date'
    formatted_date.admin_order_field = 'date'

    def get_opex_numbers(self, obj):
        return ", ".join([o.opex_number for o in obj.opex_details.all()])
    get_opex_numbers.short_description = 'Opex Numbers'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        date_fields = ['date', 'po_estimate_date', 'bill_received_date', 'bill_date']
        for field in date_fields:
            if field in form.base_fields:
                form.base_fields[field].input_formats = ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']
                form.base_fields[field].widget.format = '%d-%m-%Y'
        return form
        
    fieldsets = (
        ('Basic Information', {
            'fields': ('institution', 'vehicle', 'date', 'purpose')
        }),
        ('Vendor Details', {
            'fields': ('vendor', 'vendor_manual')
        }),
        ('Budget Details', {
            'fields': ('budget_head', 'sub_budget_head')
        }),
        ('PO / Estimate Details', {
            'fields': ('po_estimate_no', 'po_estimate_date', 'po_estimate_amount')
        }),
        ('Bill Details', {
            'fields': ('bill_no', 'bill_date', 'bill_received_date', 'bill_description', 'service_km')
        }),
        ('Amount Details', {
            'fields': ('amount', 'sgst', 'cgst', 'total_amount')
        }),
        ('Other Details', {
            'fields': ('remarks',)
        }),
        ('Audit Log', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'student_name', 'rider_type', 'institution', 'academic_year', 'year_of_study', 'allocated_vehicle', 'fee_demand', 'fee_paid', 'status', 'surrender_date', 'surrender_reason')
    list_filter = ('rider_type', 'institution', 'academic_year', 'year_of_study', 'status', 'allocated_vehicle', 'surrender_date')
    search_fields = ('roll_number', 'student_name', 'course', 'pickup_point', 'contact_number', 'surrender_reason')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    fieldsets = (
        ('Passenger Identity', {
            'fields': ('rider_type', 'roll_number', 'student_name', 'institution', 'academic_year', 'course', 'year_of_study')
        }),
        ('Transport & Route Allocation', {
            'fields': ('allocated_vehicle', 'route_name', 'pickup_point', 'drop_point')
        }),
        ('Fee Management', {
            'fields': ('fee_demand', 'fee_discount', 'fee_paid')
        }),
        ('Pass Surrender & Status Details', {
            'fields': ('status', 'surrender_date', 'surrender_reason', 'refund_amount', 'remarks')
        }),
        ('Contact Information', {
            'fields': ('contact_number', 'parent_contact')
        }),
        ('Audit Log', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

