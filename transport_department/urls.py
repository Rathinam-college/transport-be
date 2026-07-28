from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from . import api_views
from . import backup_views

router = DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'institutions', api_views.InstitutionViewSet)
router.register(r'registered-institutions', api_views.RegisteredInstitutionViewSet)
router.register(r'vehicles', api_views.VehicleViewSet)
router.register(r'movements', api_views.VehicleMovementViewSet)
router.register(r'fuel-data', api_views.FuelDataViewSet)
router.register(r'fuel-rates', api_views.FuelRateViewSet)
router.register(r'budget-heads', api_views.BudgetHeadViewSet)
router.register(r'sub-budget-heads', api_views.SubBudgetHeadViewSet)
router.register(r'vendors', api_views.VendorViewSet)
router.register(r'expenses', api_views.ExpenseRecordViewSet)
router.register(r'opex', api_views.OpexDetailViewSet)
router.register(r'service-requests', api_views.ServiceRequestViewSet)
router.register(r'vehicle-operational-history', api_views.VehicleOperationalHistoryViewSet)
router.register(r'renewals', api_views.VehicleRenewalViewSet)
router.register(r'vehicle-odometer-log', api_views.VehicleOdometerLogViewSet)
router.register(r'transport-summary', api_views.TransportSummaryViewSet)
router.register(r'transport-remarks', api_views.TransportRemarkViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('institution/<int:pk>/', views.institution_detail, name='institution_detail'),
    path('mobile/', views.mobile_dashboard, name='mobile_dashboard'),
    path('api/vehicle-fuel-chart/<int:vehicle_id>/', views.get_vehicle_fuel_data, name='vehicle_fuel_api'),
    path('api/backup/', backup_views.backup_database, name='backup_database'),
    path('api/restore/', backup_views.restore_database, name='restore_database'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
]
