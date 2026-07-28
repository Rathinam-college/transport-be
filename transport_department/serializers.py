from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (Institution, RegisteredInstitution, Vehicle, VehicleRenewal, VehicleMovement, FuelData, 
                     FuelRate, BudgetHead, SubBudgetHead, Vendor, ExpenseRecord, OpexDetail, ServiceRequest, VehicleOperationalHistory, VehicleOdometerLog, TransportSummary, TransportRemark)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = '__all__'

class RegisteredInstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredInstitution
        fields = '__all__'

class VehicleOperationalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleOperationalHistory
        fields = '__all__'

class VehicleRenewalSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleRenewal
        fields = '__all__'

class VehicleOdometerLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleOdometerLog
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    current_operation = serializers.SerializerMethodField()
    
    fc_expiry_date = serializers.SerializerMethodField()
    insurance_renewal_date = serializers.SerializerMethodField()
    road_tax_date = serializers.SerializerMethodField()
    green_tax_date = serializers.SerializerMethodField()
    permit_date = serializers.SerializerMethodField()
    pucc_date = serializers.SerializerMethodField()
    kerala_permit_date = serializers.SerializerMethodField()
    tiruppur_permit_date = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = '__all__'

    def get_latest_renewal_date(self, obj, doc_type):
        import datetime
        renewals = [r for r in obj.renewals.all() if r.document_type == doc_type]
        if not renewals:
            return None
        renewals.sort(key=lambda r: (r.new_expiry_date or datetime.date.min, r.created_at or datetime.datetime.min), reverse=True)
        return renewals[0].new_expiry_date

    def get_fc_expiry_date(self, obj): return self.get_latest_renewal_date(obj, 'FC')
    def get_insurance_renewal_date(self, obj): return self.get_latest_renewal_date(obj, 'Insurance')
    def get_road_tax_date(self, obj): return self.get_latest_renewal_date(obj, 'Road Tax')
    def get_green_tax_date(self, obj): return self.get_latest_renewal_date(obj, 'Green Tax')
    def get_permit_date(self, obj): return self.get_latest_renewal_date(obj, 'Permit')
    def get_pucc_date(self, obj): return self.get_latest_renewal_date(obj, 'PUCC')
    def get_kerala_permit_date(self, obj): return self.get_latest_renewal_date(obj, 'Kerala Permit')
    def get_tiruppur_permit_date(self, obj): return self.get_latest_renewal_date(obj, 'Tiruppur Permit')

    def get_current_operation(self, obj):
        import datetime
        histories = list(obj.operational_history.all())
        if not histories:
            return None
        histories.sort(key=lambda h: (h.effective_from or datetime.date.min, h.created_at or datetime.datetime.min), reverse=True)
        return VehicleOperationalHistorySerializer(histories[0]).data

class VehicleMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleMovement
        fields = '__all__'

class FuelDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelData
        fields = '__all__'

class FuelRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelRate
        fields = '__all__'

class BudgetHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetHead
        fields = ['id', 'name', 'color_code', 'institutions']

class SubBudgetHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubBudgetHead
        fields = ['id', 'budget_head', 'name', 'institutions']

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'

class OpexDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpexDetail
        fields = '__all__'
        read_only_fields = ['expense_record']

import json

class ExpenseRecordSerializer(serializers.ModelSerializer):
    opex_details = OpexDetailSerializer(many=True, required=False)

    class Meta:
        model = ExpenseRecord
        fields = '__all__'

    def to_internal_value(self, data):
        # Handle stringified opex_details when sent via FormData
        if hasattr(data, 'get') and isinstance(data.get('opex_details'), str):
            try:
                mutable_data = data.copy()
                mutable_data['opex_details'] = json.loads(data['opex_details'])
                data = mutable_data
            except Exception:
                pass
        return super().to_internal_value(data)

    def create(self, validated_data):
        opex_details_data = validated_data.pop('opex_details', [])
        expense_record = ExpenseRecord.objects.create(**validated_data)
        for opex_data in opex_details_data:
            OpexDetail.objects.create(expense_record=expense_record, **opex_data)
        return expense_record

    def update(self, instance, validated_data):
        opex_details_data = validated_data.pop('opex_details', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if opex_details_data is not None:
            instance.opex_details.all().delete()
            for opex_data in opex_details_data:
                OpexDetail.objects.create(expense_record=instance, **opex_data)
                
        return instance

class ServiceRequestSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    vehicle_number = serializers.CharField(source='vehicle.vehicle_number', read_only=True)
    vendor_name_detail = serializers.CharField(source='vendor_name.name', read_only=True)
    is_closed = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = '__all__'

    def get_is_closed(self, obj):
        return obj.expense_records.exists()

class TransportSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportSummary
        fields = '__all__'

class TransportRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportRemark
        fields = '__all__'
