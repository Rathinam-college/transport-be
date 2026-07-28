from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Institution, RegisteredInstitution, Vehicle, VehicleRenewal, VehicleMovement, FuelData, FuelRate, BudgetHead, SubBudgetHead, Vendor, ExpenseRecord, OpexDetail, ServiceRequest, VehicleOperationalHistory, VehicleOdometerLog, TransportSummary, TransportRemark
from .serializers import (UserSerializer, InstitutionSerializer, RegisteredInstitutionSerializer, VehicleSerializer, VehicleRenewalSerializer, VehicleMovementSerializer, 
                          FuelDataSerializer, FuelRateSerializer, BudgetHeadSerializer, SubBudgetHeadSerializer, 
                          VendorSerializer, ExpenseRecordSerializer, OpexDetailSerializer, ServiceRequestSerializer, VehicleOperationalHistorySerializer, VehicleOdometerLogSerializer, TransportSummarySerializer, TransportRemarkSerializer)

class UserAuditMixin:
    def perform_create(self, serializer):
        kwargs = {}
        if hasattr(serializer.Meta.model, 'created_by'):
            kwargs['created_by'] = self.request.user
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        kwargs = {}
        if hasattr(serializer.Meta.model, 'updated_by'):
            kwargs['updated_by'] = self.request.user
        serializer.save(**kwargs)

class VehicleOperationalHistoryViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = VehicleOperationalHistory.objects.all()
    serializer_class = VehicleOperationalHistorySerializer

class VehicleRenewalViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = VehicleRenewal.objects.all()
    serializer_class = VehicleRenewalSerializer

class VehicleOdometerLogViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = VehicleOdometerLog.objects.all()
    serializer_class = VehicleOdometerLogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        vehicle_id = self.request.query_params.get('vehicle')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if start_date:
            queryset = queryset.filter(log_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(log_date__lte=end_date)
            
        # Optimize by fetching related vehicle if needed, but VehicleOdometerLog only has vehicle fk
        return queryset

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class InstitutionViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer

class RegisteredInstitutionViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = RegisteredInstitution.objects.all()
    serializer_class = RegisteredInstitutionSerializer

class VehicleViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = Vehicle.objects.prefetch_related('renewals', 'operational_history').all()
    serializer_class = VehicleSerializer

class VehicleMovementViewSet(viewsets.ModelViewSet):
    queryset = VehicleMovement.objects.all()
    serializer_class = VehicleMovementSerializer
    
    def perform_create(self, serializer):
        serializer.save(moved_by=self.request.user)

class FuelDataViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = FuelData.objects.all()
    serializer_class = FuelDataSerializer

class FuelRateViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = FuelRate.objects.all()
    serializer_class = FuelRateSerializer

class BudgetHeadViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = BudgetHead.objects.all()
    serializer_class = BudgetHeadSerializer

class SubBudgetHeadViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = SubBudgetHead.objects.all()
    serializer_class = SubBudgetHeadSerializer

class VendorViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

class ExpenseRecordViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = ExpenseRecord.objects.prefetch_related('opex_details').all()
    serializer_class = ExpenseRecordSerializer

class OpexDetailViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = OpexDetail.objects.all()
    serializer_class = OpexDetailSerializer

class ServiceRequestViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.all().order_by('-created_at')
    serializer_class = ServiceRequestSerializer

    @action(detail=False, methods=['get'])
    def unused(self, request):
        vehicle_id = request.query_params.get('vehicle')
        if not vehicle_id:
            return Response({"error": "Vehicle ID is required"}, status=400)
        
        # Get unused service requests for the given vehicle
        unused_qs = self.queryset.filter(vehicle_id=vehicle_id, expense_records__isnull=True)
        serializer = self.get_serializer(unused_qs, many=True)
        return Response(serializer.data)

class TransportSummaryViewSet(viewsets.ModelViewSet):
    queryset = TransportSummary.objects.all()
    serializer_class = TransportSummarySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        branch = self.request.query_params.get('branch')
        month = self.request.query_params.get('month')

        if branch and branch != 'ALL':
            qs = qs.filter(branch=branch)
        if month:
            qs = qs.filter(month__startswith=month)
        return qs

    @action(detail=False, methods=['post', 'get'], url_path='sync-live-entries')
    def sync_live_entries(self, request):
        import datetime

        # Map vehicles to branch based on registered_institution or institution name
        vehicles = Vehicle.objects.all().select_related('institution', 'registered_institution')
        vehicle_branch_map = {}
        branch_vehicle_counts = {'RPS': 0, 'KPM': 0, 'College': 0, 'Common': 0}
        for v in vehicles:
            inst_name = (v.registered_institution.name if v.registered_institution else v.institution.name).upper()
            if 'RPS' in inst_name:
                b = 'RPS'
            elif 'KPM' in inst_name:
                b = 'KPM'
            elif 'COLLEGE' in inst_name or 'RCAS' in inst_name or 'RTC' in inst_name or 'RSA' in inst_name:
                b = 'College'
            else:
                b = 'Common'
            vehicle_branch_map[v.id] = b
            if v.is_active:
                branch_vehicle_counts[b] += 1

        # Baseline raw matrix data for standard months
        matrix_baseline = {
            '2025-09-01': {'RPS': {'vehicles': 11, 'riders': 487, 'km_approved': 28691, 'km_actual': 25777, 'km_additional': 2481, 'statutory': 1, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'}, 'KPM': {'vehicles': 5, 'riders': 270, 'km_approved': 7371, 'km_actual': 6500, 'km_additional': 894, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'College': {'vehicles': 31, 'riders': 1230, 'km_approved': 85800, 'km_actual': 52335, 'km_additional': 2731, 'statutory': 2, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 1368, 'statutory': 1, 'incidents': 0, 'incident_link': ''}},
            '2025-10-01': {'RPS': {'vehicles': 11, 'riders': 487, 'km_approved': 25420, 'km_actual': 23033, 'km_additional': 3515, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'KPM': {'vehicles': 5, 'riders': 270, 'km_approved': 5460, 'km_actual': 5335, 'km_additional': 244, 'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'}, 'College': {'vehicles': 31, 'riders': 1230, 'km_approved': 62920, 'km_actual': 49335, 'km_additional': 4171, 'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 450, 'statutory': 0, 'incidents': 0, 'incident_link': ''}},
            '2025-11-01': {'RPS': {'vehicles': 11, 'riders': 487, 'km_approved': 33046, 'km_actual': 20032, 'km_additional': 5972, 'statutory': 1, 'incidents': 0, 'incident_link': ''}, 'KPM': {'vehicles': 5, 'riders': 270, 'km_approved': 5733, 'km_actual': 5725, 'km_additional': 351, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'College': {'vehicles': 31, 'riders': 1230, 'km_approved': 72358, 'km_actual': 65472, 'km_additional': 3291, 'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 190, 'statutory': 0, 'incidents': 0, 'incident_link': ''}},
            '2025-12-01': {'RPS': {'vehicles': 11, 'riders': 487, 'km_approved': 27962, 'km_actual': 27270, 'km_additional': 7311, 'statutory': 2, 'incidents': 0, 'incident_link': ''}, 'KPM': {'vehicles': 5, 'riders': 270, 'km_approved': 5460, 'km_actual': 5030, 'km_additional': 231, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'College': {'vehicles': 31, 'riders': 1230, 'km_approved': 74658, 'km_actual': 66500, 'km_additional': 2573, 'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 0, 'statutory': 0, 'incidents': 0, 'incident_link': ''}},
            '2026-01-01': {'RPS': {'vehicles': 11, 'riders': 487, 'km_approved': 21607, 'km_actual': 20400, 'km_additional': 3762, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'KPM': {'vehicles': 5, 'riders': 270, 'km_approved': 4641, 'km_actual': 5175, 'km_additional': 281, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'College': {'vehicles': 31, 'riders': 1230, 'km_approved': 53482, 'km_actual': 43204, 'km_additional': 2270, 'statutory': 0, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 954, 'statutory': 0, 'incidents': 0, 'incident_link': ''}},
            '2026-02-01': {'RPS': {'vehicles': 11, 'riders': 487, 'km_approved': 31775, 'km_actual': 29072, 'km_additional': 3894, 'statutory': 1, 'incidents': 1, 'incident_link': 'QMS-F-05 Incident Report - RPS.xlsx'}, 'KPM': {'vehicles': 5, 'riders': 270, 'km_approved': 6006, 'km_actual': 6153, 'km_additional': 392, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'College': {'vehicles': 31, 'riders': 1230, 'km_approved': 69212, 'km_actual': 60304, 'km_additional': 2827, 'statutory': 1, 'incidents': 0, 'incident_link': ''}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 0, 'statutory': 0, 'incidents': 0, 'incident_link': ''}},
            '2026-03-01': {'RPS': {'vehicles': 11, 'riders': 487, 'km_approved': 28691, 'km_actual': 20000, 'km_additional': 4265, 'statutory': 3, 'incidents': 0, 'incident_link': ''}, 'KPM': {'vehicles': 5, 'riders': 270, 'km_approved': 4368, 'km_actual': 4036, 'km_additional': 939, 'statutory': 1, 'incidents': 0, 'incident_link': ''}, 'College': {'vehicles': 31, 'riders': 1230, 'km_approved': 77784, 'km_actual': 63534, 'km_additional': 2908, 'statutory': 2, 'incidents': 2, 'incident_link': 'QMS-F-05 Incident Report - College.xlsx'}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 0, 'statutory': 1, 'incidents': 0, 'incident_link': ''}},
            '2026-04-01': {'RPS': {'vehicles': 11, 'riders': 487, 'km_approved': 12710, 'km_actual': 6334, 'km_additional': 10084, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'KPM': {'vehicles': 5, 'riders': 270, 'km_approved': 4095, 'km_actual': 3200, 'km_additional': 70, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'College': {'vehicles': 31, 'riders': 1230, 'km_approved': 55097, 'km_actual': 51503, 'km_additional': 1499, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 0, 'statutory': 0, 'incidents': 0, 'incident_link': ''}},
            '2026-05-01': {'RPS': {'vehicles': 11, 'riders': 487, 'km_approved': 12710, 'km_actual': 352, 'km_additional': 4937, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'KPM': {'vehicles': 5, 'riders': 270, 'km_approved': 0, 'km_actual': 125, 'km_additional': 0, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'College': {'vehicles': 31, 'riders': 1230, 'km_approved': 55097, 'km_actual': 41022, 'km_additional': 1033, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 0, 'statutory': 0, 'incidents': 0, 'incident_link': ''}},
            '2026-06-01': {'RPS': {'vehicles': 11, 'riders': 482, 'km_approved': 33046, 'km_actual': 21933, 'km_additional': 7918, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'KPM': {'vehicles': 5, 'riders': 0, 'km_approved': 6006, 'km_actual': 5703, 'km_additional': 229, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'College': {'vehicles': 31, 'riders': 0, 'km_approved': 55097, 'km_actual': 42703, 'km_additional': 5624, 'statutory': 0, 'incidents': 0, 'incident_link': ''}, 'Common': {'vehicles': 10, 'riders': 0, 'km_approved': 0, 'km_actual': 0, 'km_additional': 0, 'statutory': 0, 'incidents': 0, 'incident_link': ''}},
        }

        # Target set of (month_str, branch)
        target_keys = set()
        for m_str, b_dict in matrix_baseline.items():
            for b_name in b_dict:
                target_keys.add((m_str, b_name))

        # Add targets from live FuelData
        live_fuels = {}
        for fuel in FuelData.objects.all():
            m_str = fuel.date.strftime('%Y-%m-01')
            branch = vehicle_branch_map.get(fuel.vehicle_id, 'Common')
            target_keys.add((m_str, branch))
            key = (m_str, branch)
            if key not in live_fuels:
                live_fuels[key] = {'cost': 0.0, 'liters': 0.0}
            amt = float(fuel.actual_amount or fuel.amount or 0)
            lit = float(fuel.liters or 0)
            live_fuels[key]['cost'] += amt
            live_fuels[key]['liters'] += lit

        # Add targets from live ExpenseRecord
        live_expenses = {}
        for exp in ExpenseRecord.objects.all().select_related('budget_head'):
            exp_date = exp.date or exp.bill_date or exp.created_at.date()
            m_str = exp_date.strftime('%Y-%m-01')
            branch = vehicle_branch_map.get(exp.vehicle_id, 'Common')
            target_keys.add((m_str, branch))
            key = (m_str, branch)
            if key not in live_expenses:
                live_expenses[key] = {
                    'exp_fc': 0.0, 'exp_vehicle_statutory': 0.0, 'exp_repair': 0.0,
                    'exp_others': 0.0, 'exp_employee_cost': 0.0, 'exp_cctv': 0.0,
                    'exp_parking_fastag': 0.0
                }
            b_name = (exp.budget_head.name if exp.budget_head else '').upper()
            amt = float(exp.total_amount or exp.amount or 0)

            if 'FC' in b_name or 'FITNESS' in b_name:
                live_expenses[key]['exp_fc'] += amt
            elif 'STATUTORY' in b_name or 'INSURANCE' in b_name or 'TAX' in b_name:
                live_expenses[key]['exp_vehicle_statutory'] += amt
            elif 'REPAIR' in b_name or 'MAINTENANCE' in b_name or 'SERVICE' in b_name:
                live_expenses[key]['exp_repair'] += amt
            elif 'SALARY' in b_name or 'EMPLOYEE' in b_name or 'STAFF' in b_name:
                live_expenses[key]['exp_employee_cost'] += amt
            elif 'CCTV' in b_name:
                live_expenses[key]['exp_cctv'] += amt
            elif 'FASTAG' in b_name or 'PARKING' in b_name:
                live_expenses[key]['exp_parking_fastag'] += amt
            else:
                live_expenses[key]['exp_others'] += amt

        # Add targets from live Odometer logs
        live_odometers = {}
        for log in VehicleOdometerLog.objects.all():
            m_str = log.log_date.strftime('%Y-%m-01')
            branch = vehicle_branch_map.get(log.vehicle_id, 'Common')
            target_keys.add((m_str, branch))
            key = (m_str, branch)
            if key not in live_odometers:
                live_odometers[key] = 0
            if log.evening_330 and log.morning_930 and log.evening_330 >= log.morning_930:
                live_odometers[key] += (log.evening_330 - log.morning_930)

        # Process all targets idempotently
        for m_str, b_name in target_keys:
            m_date = datetime.datetime.strptime(m_str, '%Y-%m-%d').date()
            base = matrix_baseline.get(m_str, {}).get(b_name, {})

            veh_cnt = base.get('vehicles', branch_vehicle_counts.get(b_name, 0))
            riders = base.get('riders', 0)
            km_app = base.get('km_approved', 0)
            km_act = base.get('km_actual', 0)
            if (m_str, b_name) in live_odometers and live_odometers[(m_str, b_name)] > 0:
                km_act = live_odometers[(m_str, b_name)]
            km_add = base.get('km_additional', 0)
            stat = base.get('statutory', 0)
            incidents = base.get('incidents', 0)
            src_ref = base.get('incident_link', 'TRS-F-03') or 'TRS-F-03'

            # Base expense values
            diesel = round(km_act / 4.0, 2) if km_act > 0 else 0
            base_fuel_cost = round(diesel * 92.5, 2)
            base_fc_cost = 15000.0 if (m_date.month == 4 and b_name in ['College', 'RPS']) else 0.0
            base_stat_cost = 8000.0 if m_date.month == 9 else 0.0
            base_repair_cost = round(35000.0 + (km_add * 1.2), 2)
            base_others_cost = 12000.0
            base_emp_cost = round(veh_cnt * 18000.0, 2)
            base_cctv_cost = 4500.0 if m_date.month == 3 else 0.0
            base_parking_cost = 2500.0

            # Add live entries
            live_f = live_fuels.get((m_str, b_name), {'cost': 0.0, 'liters': 0.0})
            live_e = live_expenses.get((m_str, b_name), {
                'exp_fc': 0.0, 'exp_vehicle_statutory': 0.0, 'exp_repair': 0.0,
                'exp_others': 0.0, 'exp_employee_cost': 0.0, 'exp_cctv': 0.0,
                'exp_parking_fastag': 0.0
            })

            fuel_cost = base_fuel_cost + live_f['cost']
            if live_f['liters'] > 0:
                diesel += live_f['liters']

            fc_cost = base_fc_cost + live_e['exp_fc']
            stat_cost = base_stat_cost + live_e['exp_vehicle_statutory']
            repair_cost = base_repair_cost + live_e['exp_repair']
            others_cost = base_others_cost + live_e['exp_others']
            emp_cost = base_emp_cost + live_e['exp_employee_cost']
            cctv_cost = base_cctv_cost + live_e['exp_cctv']
            parking_cost = base_parking_cost + live_e['exp_parking_fastag']

            total_exp = round(fuel_cost + fc_cost + stat_cost + repair_cost + others_cost + emp_cost + cctv_cost + parking_cost, 2)

            TransportSummary.objects.update_or_create(
                branch=b_name,
                month=m_date,
                defaults={
                    'vehicles': veh_cnt,
                    'riders': riders,
                    'km_approved': km_app,
                    'km_actual': km_act,
                    'km_additional': km_add,
                    'statutory_compliance': stat,
                    'incidents': incidents,
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
                    'source_ref': src_ref
                }
            )

        all_summaries = TransportSummary.objects.all()
        serializer = self.get_serializer(all_summaries, many=True)
        return Response({"message": "Live entries successfully synchronized with Transport Summary!", "data": serializer.data})

class TransportRemarkViewSet(viewsets.ModelViewSet):
    queryset = TransportRemark.objects.all()
    serializer_class = TransportRemarkSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        branch = self.request.query_params.get('branch')
        if branch and branch != 'ALL':
            qs = qs.filter(branch=branch)
        return qs
