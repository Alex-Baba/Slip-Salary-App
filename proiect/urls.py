"""
URL configuration for proiect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from app.api.routers.health import HealthCheckView
from app.api.routers.employee import (
    EmployeeCreateView, EmployeeListView, EmployeeDeleteView, EmployeeUpdateView
)
from app.api.routers.department import (
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView, DepartmentDeleteView
)
from app.db.models import EmployeeRole
from rest_framework.views import APIView
from rest_framework.response import Response
from app.api.routers.manager import ManagerListView, DepartmentManagersView
from app.api.routers.attendance import AttendanceUpsertView, AttendanceUpdateView, AttendanceListView
from app.api.routers.aggregateEmployeeData import AggregateEmployeeDataView
from app.api.routers.bonus import BonusCreateView, BonusListView, BonusUpdateView, BonusDeleteView
from app.api.routers.createPdfEmployees import CreatePdfEmployeesView
from app.api.routers.sendPdfToEmployees import SendPayslipEmailView
from app.api.routers.auth import LoginView
from app.api.routers.me import MeView
from app.api.routers.sendAggregatedCsvEmail import SendAggregatedCsvEmailView
from app.api.routers.sendManagerAggregatedCsvEmail import SendManagerAggregatedCsvEmailView

class RoleListView(APIView):
    def get(self, request):
        roles = list(EmployeeRole.objects.values('id','role'))
        return Response(roles)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/employees/', EmployeeCreateView.as_view(), name='employee-create'),
    path('api/employees_all/', EmployeeListView.as_view(), name='employee-list'),
    path('api/employees/<int:employee_id>/update/', EmployeeUpdateView.as_view(), name='employee-update'),
    path('api/employees/<int:employee_id>/delete/', EmployeeDeleteView.as_view(), name='employee-delete'),
    path('api/roles/', RoleListView.as_view(), name='role-list'),
    path('api/departments/list/', DepartmentListView.as_view(), name='department-list'),
    path('api/departments/create/', DepartmentCreateView.as_view(), name='department-create'),
    path('api/departments/<int:department_id>/update/', DepartmentUpdateView.as_view(), name='department-update'),
    path('api/departments/<int:department_id>/delete/', DepartmentDeleteView.as_view(), name='department-delete'),
    path('api/managers/', ManagerListView.as_view(), name='manager-list'),
    path('api/departments/<int:department_id>/managers/', DepartmentManagersView.as_view(), name='department-managers'),
    path('api/attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('api/attendance/upsert/', AttendanceUpsertView.as_view(), name='attendance-upsert'),
    path('api/attendance/<int:attendance_id>/update/', AttendanceUpdateView.as_view(), name='attendance-update'),
    path('api/employees/aggregate_data/', AggregateEmployeeDataView.as_view(), name='aggregate-employee-data'),
    path('api/bonuses/create/', BonusCreateView.as_view(), name='bonus-create'),
    path('api/bonuses/list/', BonusListView.as_view(), name='bonus-list'),
    path('api/bonuses/<int:bonus_id>/update/', BonusUpdateView.as_view(), name='bonus-update'),
    path('api/bonuses/<int:bonus_id>/delete/', BonusDeleteView.as_view(), name='bonus-delete'),
    path('api/employees/create_pdf/', CreatePdfEmployeesView.as_view(), name='create-pdf-employees'),
    path('api/employees/send_payslip_email/', SendPayslipEmailView.as_view(), name='send-payslip-email'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/me/', MeView.as_view(), name='me'),
    path('api/employees/send_aggregated_csv_email/', SendAggregatedCsvEmailView.as_view(), name='send-aggregated-csv-email'),
    path('api/employees/send_manager_aggregated_csv_email/', SendManagerAggregatedCsvEmailView.as_view(), name='send-manager-aggregated-csv-email'),
]
