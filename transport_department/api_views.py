from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (Institution, RegisteredInstitution, Vehicle, VehicleRenewal, VehicleMovement, FuelData, 
                     FuelRate, BudgetHead, SubBudgetHead, Vendor, ExpenseRecord, OpexDetail, ServiceRequest, 
                     VehicleOperationalHistory, VehicleOdometerLog, TransportRemark, Student)
from .serializers import (UserSerializer, InstitutionSerializer, RegisteredInstitutionSerializer, VehicleSerializer, VehicleRenewalSerializer, VehicleMovementSerializer, 
                          FuelDataSerializer, FuelRateSerializer, BudgetHeadSerializer, SubBudgetHeadSerializer, 
                          VendorSerializer, ExpenseRecordSerializer, OpexDetailSerializer, ServiceRequestSerializer, 
                          VehicleOperationalHistorySerializer, VehicleOdometerLogSerializer, 
                          TransportRemarkSerializer, StudentSerializer)


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

class TransportSummaryViewSet(viewsets.ViewSet):
    
    def list(self, request):
        import datetime

        branch_filter = request.query_params.get('branch')
        month_filter = request.query_params.get('month')
        results = []

        # Map vehicles to branch based on registered_institution or institution name
        vehicles = Vehicle.objects.all().select_related('institution', 'registered_institution')
        vehicle_branch_map = {}
        branch_vehicle_counts = {'RPS': 0, 'KPM': 0, 'University': 0, 'Common': 0}
        for v in vehicles:
            inst_name = (v.registered_institution.name if v.registered_institution else v.institution.name).upper()
            if 'RPS' in inst_name:
                b = 'RPS'
            elif 'KPM' in inst_name:
                b = 'KPM'
            elif 'UNIVERSITY' in inst_name or 'COLLEGE' in inst_name or 'RCAS' in inst_name or 'RTC' in inst_name or 'RSA' in inst_name:
                b = 'University'
            else:
                b = 'Common'
            vehicle_branch_map[v.id] = b
            if v.is_active:
                branch_vehicle_counts[b] += 1

        # Target set of (month_str, branch) initialized with the current month for all branches
        # so that there is always at least one row in the report even if DB is empty.
        target_keys = set()
        current_month_str = datetime.date.today().replace(day=1).strftime('%Y-%m-01')
        for b_name in ['RPS', 'KPM', 'University', 'Common']:
            target_keys.add((current_month_str, b_name))

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

        # Add targets from live Student entries for active ridership
        live_riders = {}
        for student in Student.objects.filter(status='Active'):
            if not student.allocated_vehicle_id:
                continue
            branch = vehicle_branch_map.get(student.allocated_vehicle_id, 'Common')
            if branch not in live_riders:
                live_riders[branch] = 0
            live_riders[branch] += 1

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

            veh_cnt = branch_vehicle_counts.get(b_name, 0)
            riders = live_riders.get(b_name, 0)
            km_app = 0
            km_act = 0
            if (m_str, b_name) in live_odometers and live_odometers[(m_str, b_name)] > 0:
                km_act = live_odometers[(m_str, b_name)]
            km_add = 0
            stat = 0
            incidents = 0
            src_ref = 'TRS-F-03'

            # Add live entries
            live_f = live_fuels.get((m_str, b_name), {'cost': 0.0, 'liters': 0.0})
            live_e = live_expenses.get((m_str, b_name), {
                'exp_fc': 0.0, 'exp_vehicle_statutory': 0.0, 'exp_repair': 0.0,
                'exp_others': 0.0, 'exp_employee_cost': 0.0, 'exp_cctv': 0.0,
                'exp_parking_fastag': 0.0
            })

            fuel_cost = round(live_f['cost'], 2)
            diesel = round(live_f['liters'], 2)

            fc_cost = round(live_e['exp_fc'], 2)
            stat_cost = round(live_e['exp_vehicle_statutory'], 2)
            repair_cost = round(live_e['exp_repair'], 2)
            others_cost = round(live_e['exp_others'], 2)
            emp_cost = round(live_e['exp_employee_cost'], 2)
            cctv_cost = round(live_e['exp_cctv'], 2)
            parking_cost = round(live_e['exp_parking_fastag'], 2)

            total_exp = round(fuel_cost + fc_cost + stat_cost + repair_cost + others_cost + emp_cost + cctv_cost + parking_cost, 2)

            summary_item = {
                'id': f"{m_str}-{b_name}",
                'branch': b_name,
                'month': m_str,
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
                'budget_approved': 0,
                'budget_spent_cumulative': total_exp,
                'budget_balance': 0 - total_exp,
                'fee_demand': 0,
                'fee_discount': 0,
                'fee_paid': 0,
                'fee_unpaid': 0,
                'cost_per_student': round(total_exp / riders, 2) if riders > 0 else 0,
                'fee_per_student_year': 0,
                'feedback_score': 1.0,
                'cab_request_billing': 0,
                'source_ref': src_ref
            }

            if branch_filter and branch_filter != 'ALL' and b_name != branch_filter:
                continue
            if month_filter and not m_str.startswith(month_filter):
                continue
            
            results.append(summary_item)

        return Response(results)

class TransportRemarkViewSet(viewsets.ModelViewSet):
    queryset = TransportRemark.objects.all()
    serializer_class = TransportRemarkSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        branch = self.request.query_params.get('branch')
        if branch and branch != 'ALL':
            qs = qs.filter(branch=branch)
        return qs


class StudentViewSet(UserAuditMixin, viewsets.ModelViewSet):
    queryset = Student.objects.select_related('institution', 'allocated_vehicle').all()
    serializer_class = StudentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        inst_id = self.request.query_params.get('institution')
        academic_year = self.request.query_params.get('academic_year')
        year_of_study = self.request.query_params.get('year_of_study')
        vehicle_id = self.request.query_params.get('vehicle')
        status = self.request.query_params.get('status')
        search = self.request.query_params.get('search')

        rider_type = self.request.query_params.get('rider_type', None)
        if rider_type:
            qs = qs.filter(rider_type=rider_type)
        if inst_id:
            qs = qs.filter(institution_id=inst_id)
        if academic_year:
            qs = qs.filter(academic_year=academic_year)
        if year_of_study:
            qs = qs.filter(year_of_study=year_of_study)
        if vehicle_id:
            if vehicle_id == 'unallocated':
                qs = qs.filter(allocated_vehicle__isnull=True)
            else:
                qs = qs.filter(allocated_vehicle_id=vehicle_id)
        if status:
            qs = qs.filter(status=status)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(student_name__icontains=search) | 
                Q(roll_number__icontains=search) | 
                Q(course__icontains=search) |
                Q(pickup_point__icontains=search) |
                Q(route_name__icontains=search)
            )
        return qs

    @action(detail=True, methods=['post'])
    def allocate_vehicle(self, request, pk=None):
        student = self.get_object()
        vehicle_id = request.data.get('allocated_vehicle')
        route_name = request.data.get('route_name')
        pickup_point = request.data.get('pickup_point')
        drop_point = request.data.get('drop_point')

        if vehicle_id is not None:
            student.allocated_vehicle_id = vehicle_id if vehicle_id != '' else None
        if route_name is not None:
            student.route_name = route_name
        if pickup_point is not None:
            student.pickup_point = pickup_point
        if drop_point is not None:
            student.drop_point = drop_point

        if request.user.is_authenticated:
            student.updated_by = request.user
        student.save()

        serializer = self.get_serializer(student)
        return Response({
            'message': f'Bus allocation for {student.student_name} updated successfully.',
            'student': serializer.data
        })

    @action(detail=True, methods=['post'])
    def surrender_pass(self, request, pk=None):
        student = self.get_object()
        surrender_date = request.data.get('surrender_date') or timezone.now().date()
        surrender_reason = request.data.get('surrender_reason') or 'Pass Surrendered'
        refund_amount = float(request.data.get('refund_amount') or 0)
        remarks = request.data.get('remarks', '')

        student.status = 'Pass Surrendered'
        student.surrender_date = surrender_date
        student.surrender_reason = surrender_reason
        student.refund_amount = refund_amount
        if remarks:
            student.remarks = remarks
        if request.user.is_authenticated:
            student.updated_by = request.user
        student.save()

        serializer = self.get_serializer(student)
        return Response({
            'message': f'Bus pass for {student.student_name} ({student.roll_number}) surrendered successfully. Historical record preserved.',
            'student': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reactivate_pass(self, request, pk=None):
        student = self.get_object()
        allocated_vehicle_id = request.data.get('allocated_vehicle')
        
        student.status = 'Active'
        if allocated_vehicle_id is not None:
            student.allocated_vehicle_id = allocated_vehicle_id if allocated_vehicle_id != '' else None
        
        if request.user.is_authenticated:
            student.updated_by = request.user
        student.save()

        serializer = self.get_serializer(student)
        return Response({
            'message': f'Bus pass for {student.student_name} ({student.roll_number}) reactivated successfully.',
            'student': serializer.data
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        from django.db.models import Sum, Count
        qs = self.get_queryset()
        
        total_students = qs.count()
        active_count = qs.filter(status='Active').count()
        surrendered_count = qs.filter(status='Pass Surrendered').count()
        allocated_count = qs.filter(allocated_vehicle__isnull=False, status='Active').count()
        unallocated_count = active_count - allocated_count
        
        demand_sum = qs.aggregate(s=Sum('fee_demand'))['s'] or 0
        discount_sum = qs.aggregate(s=Sum('fee_discount'))['s'] or 0
        paid_sum = qs.aggregate(s=Sum('fee_paid'))['s'] or 0
        refund_sum = qs.aggregate(s=Sum('refund_amount'))['s'] or 0
        
        net_demand = max(0, float(demand_sum) - float(discount_sum))
        balance_due = max(0, net_demand - float(paid_sum))

        return Response({
            'total_students': total_students,
            'active_count': active_count,
            'surrendered_count': surrendered_count,
            'allocated_count': allocated_count,
            'unallocated_count': unallocated_count,
            'allocation_rate': round((allocated_count / (active_count or 1)) * 100, 1),
            'total_fee_demand': float(demand_sum),
            'total_fee_discount': float(discount_sum),
            'total_fee_paid': float(paid_sum),
            'total_refund_amount': float(refund_sum),
            'net_fee_collected': max(0, float(paid_sum) - float(refund_sum)),
            'total_balance_due': balance_due,
        })


