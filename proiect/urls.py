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
from app.api.routers.employee import EmployeeCreateView, EmployeeListView, EmployeeDeleteView
from app.api.routers.department import DepartmentListView, DepartmentCreateView
from app.db.models import EmployeeRole
from rest_framework.views import APIView
from rest_framework.response import Response
from app.api.routers.manager import ManagerListView, DepartmentManagersView
from app.api.routers.attendance import AttendanceUpsertView, AttendanceUpdateView, AttendanceListView


class RoleListView(APIView):
    def get(self, request):
        roles = list(EmployeeRole.objects.values('id','role'))
        return Response(roles)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/employees/', EmployeeCreateView.as_view(), name='employee-create'),
    path('api/employees_all/', EmployeeListView.as_view(), name='employee-list'),
    path('api/roles/', RoleListView.as_view(), name='role-list'),
    path('api/departments/list/', DepartmentListView.as_view(), name='department-list'),
    path('api/departments/create/', DepartmentCreateView.as_view(), name='department-create'),
    path('api/managers/', ManagerListView.as_view(), name='manager-list'),
    path('api/departments/<int:department_id>/managers/', DepartmentManagersView.as_view(), name='department-managers'),
    path('api/attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('api/attendance/upsert/', AttendanceUpsertView.as_view(), name='attendance-upsert'),
    path('api/attendance/<int:attendance_id>/update/', AttendanceUpdateView.as_view(), name='attendance-update'),
    path('api/employees/<int:employee_id>/delete/', EmployeeDeleteView.as_view(), name='employee-delete'),
]
