from django.db import models
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum, Subquery, OuterRef
from django.http import JsonResponse
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from .models import Institution, Vehicle, FuelData, ExpenseRecord, VehicleMovement
from django.utils import timezone
from datetime import date, timedelta

# Create your views here.
def index(request):
    return dashboard(request)

def dashboard(request):
    # Date Calculations
    now = timezone.now()
    first_day_current = now.replace(day=1)
    last_day_prev = first_day_current - timedelta(days=1)
    first_day_prev = last_day_prev.replace(day=1)

    # Subqueries for Institution Stats
    current_fuel_sq = FuelData.objects.filter(
        institution=OuterRef('pk'),
        date__gte=first_day_current
    ).values('institution').annotate(total=Sum('amount')).values('total')

    prev_fuel_sq = FuelData.objects.filter(
        institution=OuterRef('pk'),
        date__gte=first_day_prev,
        date__lte=last_day_prev
    ).values('institution').annotate(total=Sum('amount')).values('total')

    total_expense_sq = ExpenseRecord.objects.filter(
        institution=OuterRef('pk')
    ).values('institution').annotate(total=Sum('total_amount')).values('total')

    institutions = Institution.objects.annotate(
        vehicle_count=Count('vehicles'),
        curr_month_fuel=Subquery(current_fuel_sq),
        prev_month_fuel=Subquery(prev_fuel_sq),
        total_expenses=Subquery(total_expense_sq)
    )
    
    # Summary Statistics
    total_vehicles = Vehicle.objects.count()
    total_fuel_amount = FuelData.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense_amount = ExpenseRecord.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_institutions = institutions.count()

    context = {
        'institutions': institutions,
        'stats': {
            'total_vehicles': total_vehicles,
            'total_institutions': total_institutions,
            'total_fuel': total_fuel_amount,
            'total_expense': total_expense_amount,
        }
    }
    return render(request, 'transport_department/dashboard.html', context)


def institution_detail(request, pk, template_name='transport_department/institution_detail.html'):
    institution = get_object_or_404(Institution, pk=pk)
    vehicles = institution.vehicles.all()
    
    fuel_stats = FuelData.objects.filter(institution=institution).aggregate(
        total_liters=Sum('liters'),
        total_amount=Sum('amount')
    )
    
    expense_stats = ExpenseRecord.objects.filter(institution=institution).aggregate(
        total_amount=Sum('total_amount')
    )
    
    # Breakdown by Budget Head
    budget_breakdown = ExpenseRecord.objects.filter(institution=institution).values(
        'budget_head__name'
    ).annotate(total=Sum('total_amount')).order_by('-total')

    # Breakdown by Budget Head
    budget_breakdown = ExpenseRecord.objects.filter(institution=institution).values(
        'budget_head__name'
    ).annotate(total=Sum('total_amount')).order_by('-total')

    # Recent Movements
    recent_movements = VehicleMovement.objects.filter(
        models.Q(from_institution=institution) | models.Q(to_institution=institution)
    ).order_by('-moved_at')[:10]

    # --- Month & Year Picker Filtering ---
    import calendar
    now = timezone.now()
    
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')
    
    if selected_month and selected_year:
        try:
            month = int(selected_month)
            year = int(selected_year)
        except ValueError:
            month = now.month
            year = now.year
    else:
        month = now.month
        year = now.year

    # Calculate first and last day of the selected month
    start_date = date(year, month, 1)
    num_days = calendar.monthrange(year, month)[1]
    end_date = date(year, month, num_days)

    # Generate list of dates for the entire month
    date_list = [date(year, month, d) for d in range(1, num_days + 1)]
    
    # Month list for dropdown
    months_choices = [(i, calendar.month_name[i]) for i in range(1, 13)]
    # Year list for dropdown (last 5 years)
    years_choices = range(now.year - 4, now.year + 1)

    # Fetch all relevant records for the range
    fuel_data = FuelData.objects.filter(
        vehicle__institution=institution,
        date__range=[start_date, end_date]
    ).values('vehicle_id', 'date').annotate(total=Sum('amount'))

    expense_data = ExpenseRecord.objects.filter(
        vehicle__institution=institution,
        date__range=[start_date, end_date]
    ).values('vehicle_id', 'date').annotate(total=Sum('total_amount'))

    # Build Matrix: { vehicle_id: { date_obj: amount } }
    matrix = {}
    col_totals = {d: 0 for d in date_list}
    grand_total = 0

    for v in vehicles:
        matrix[v.id] = {d: 0 for d in date_list}
        matrix[v.id]['row_total'] = 0
        matrix[v.id]['vehicle_obj'] = v

    # Fill fuel
    for entry in fuel_data:
        d = entry['date']
        vid = entry['vehicle_id']
        amt = float(entry['total'] or 0)
        if vid in matrix and d in matrix[vid]:
            matrix[vid][d] += amt
            matrix[vid]['row_total'] += amt
            col_totals[d] += amt
            grand_total += amt

    # Fill expenses
    for entry in expense_data:
        d = entry['date']
        vid = entry['vehicle_id']
        amt = float(entry['total'] or 0)
        if vid in matrix and d in matrix[vid]:
            matrix[vid][d] += amt
            matrix[vid]['row_total'] += amt
            col_totals[d] += amt
            grand_total += amt

    # Matrix List for template
    matrix_list = []
    for vid, data in matrix.items():
        row_cells = [data[d] for d in date_list]
        matrix_list.append({
            'vehicle': data['vehicle_obj'],
            'cells': row_cells,
            'total': data['row_total']
        })
    
    col_totals_list = [col_totals[d] for d in date_list]

    # --- Advanced Analytics ---
    # 1. Budget Distribution for Chart
    budget_dist = list(budget_breakdown)
    
    # 2. Top Spending Vehicle this month (Calculate manually from matrix to be accurate)
    top_vehicle = None
    if matrix_list:
        sorted_matrix = sorted(matrix_list, key=lambda x: x['total'], reverse=True)
        top_vehicle = sorted_matrix[0]['vehicle'] if sorted_matrix[0]['total'] > 0 else None

    # 3. Month-over-Month Growth
    import datetime
    try:
        prev_month_end = start_date - datetime.timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        
        prev_fuel = FuelData.objects.filter(vehicle__institution=institution, date__range=[prev_month_start, prev_month_end]).aggregate(total=Sum('amount'))['total'] or 0
        prev_exp = ExpenseRecord.objects.filter(vehicle__institution=institution, date__range=[prev_month_start, prev_month_end]).aggregate(total=Sum('total_amount'))['total'] or 0
        prev_total = float(prev_fuel + prev_exp)
        
        current_total = float(grand_total)
        if prev_total > 0:
            mom_growth = ((current_total - prev_total) / prev_total) * 100
        else:
            mom_growth = 0
    except:
        mom_growth = 0

    # 4. Financial Activity Feed (Unify fields for template)
    recent_fuel = FuelData.objects.filter(vehicle__institution=institution).order_by('-date')[:10]
    recent_gen_exp = ExpenseRecord.objects.filter(institution=institution).order_by('-date')[:10]
    
    activity_list = list(recent_fuel) + list(recent_gen_exp)
    for item in activity_list:
        if hasattr(item, 'amount'):
            item.display_amount = item.amount
            item.activity_type = 'Fuel'
        else:
            item.display_amount = item.total_amount
            item.activity_type = 'Expense'

    financial_activity = sorted(
        activity_list,
        key=lambda x: x.date,
        reverse=True
    )[:10]

    context = {
        'institution': institution,
        'vehicles': vehicles,
        'fuel': fuel_stats,
        'expenses': expense_stats,
        'budget_breakdown': budget_breakdown,
        'recent_movements': recent_movements,
        'matrix_list': matrix_list,
        'days': date_list, 
        'col_totals_list': col_totals_list,
        'grand_total': grand_total,
        'months_choices': months_choices,
        'years_choices': years_choices,
        'selected_month': month,
        'selected_year': year,
        'range_display': f"{calendar.month_name[month]} {year}",
        'top_vehicle': top_vehicle,
        'mom_growth': mom_growth,
        'budget_dist': budget_dist,
        'financial_activity': financial_activity,
    }
    return render(request, template_name, context)


def get_vehicle_fuel_data(request, vehicle_id):
    period = request.GET.get('period', 'day')
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    
    queryset = FuelData.objects.filter(vehicle=vehicle)
    
    if period == 'day':
        # Group by day for the last 30 entries
        data = queryset.annotate(label=TruncDay('date')).values('label').annotate(
            total_liters=Sum('liters'), 
            total_amount=Sum('amount')
        ).order_by('label')
    elif period == 'month':
        data = queryset.annotate(label=TruncMonth('date')).values('label').annotate(
            total_liters=Sum('liters'), 
            total_amount=Sum('amount')
        ).order_by('label')
    elif period == 'year':
        data = queryset.annotate(label=TruncYear('date')).values('label').annotate(
            total_liters=Sum('liters'), 
            total_amount=Sum('amount')
        ).order_by('label')
    else:
        return JsonResponse({'error': 'Invalid period'}, status=400)

    result = {
        'vehicle_number': vehicle.vehicle_number,
        'labels': [item['label'].strftime('%d-%m-%Y' if period=='day' else '%b %Y' if period=='month' else '%Y') for item in data],
        'liters': [float(item['total_liters']) for item in data],
        'amounts': [float(item['total_amount']) for item in data],
    }
    return JsonResponse(result)

def mobile_dashboard(request):
    # For demo purposes, we'll use institution 3 as the default "My Fleet"
    return institution_detail(request, 3, template_name='transport_department/mobile_dashboard.html')
