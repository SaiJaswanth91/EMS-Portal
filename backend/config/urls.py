from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from datetime import timedelta
import json
from django.db.models import Count, Q
from django.utils import timezone

from apps.accounts.models import User
from apps.employees.models import Employee, EmploymentStatus
from apps.departments.models import Department
from apps.attendance.models import Attendance, AttendanceStatus
from apps.leaves.models import LeaveRequest, LeaveRequestStatus, LeaveBalance


@login_required
def home_view(request):
    """
    Main authenticated role-aware dashboard view.
    Calculates dynamic metrics, role-scoped data, and chart payloads.
    """
    user = request.user
    today = timezone.now().date()

    context = {
        'title': 'Dashboard',
        'today_date': today,
        'user_role': user.role,
    }

    if user.role in [User.Role.ADMIN, User.Role.HR]:
        # --- ADMIN & HR SCOPE ---
        total_employees = Employee.objects.filter(employment_status=EmploymentStatus.ACTIVE).count()
        total_departments = Department.objects.filter(status=True).count()
        present_today = Attendance.objects.filter(
            date=today,
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]
        ).count()
        pending_leaves = LeaveRequest.objects.filter(status=LeaveRequestStatus.PENDING).count()

        # Chart 1: Today's Attendance Breakdown
        attendance_today_qs = Attendance.objects.filter(date=today)
        att_counts = {
            'Present': attendance_today_qs.filter(status=AttendanceStatus.PRESENT).count(),
            'Late': attendance_today_qs.filter(status=AttendanceStatus.LATE).count(),
            'Half Day': attendance_today_qs.filter(status=AttendanceStatus.HALF_DAY).count(),
            'On Leave': attendance_today_qs.filter(status=AttendanceStatus.ON_LEAVE).count(),
            'Absent': attendance_today_qs.filter(status=AttendanceStatus.ABSENT).count(),
        }

        # Chart 2: Employees by Department
        dept_qs = Department.objects.filter(status=True).annotate(
            emp_count=Count('employees', filter=Q(employees__employment_status=EmploymentStatus.ACTIVE))
        ).order_by('-emp_count', 'name')
        dept_labels = [dept.name for dept in dept_qs]
        dept_counts = [dept.emp_count for dept in dept_qs]

        # Chart 3: 7-Day Attendance Trend
        start_trend_date = today - timedelta(days=6)
        trend_dates = [(start_trend_date + timedelta(days=i)) for i in range(7)]
        trend_labels = [d.strftime('%a %d %b') for d in trend_dates]

        trend_qs = Attendance.objects.filter(
            date__gte=start_trend_date,
            date__lte=today,
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]
        ).values('date').annotate(cnt=Count('id'))
        trend_map = {item['date']: item['cnt'] for item in trend_qs}
        trend_counts = [trend_map.get(d, 0) for d in trend_dates]

        context.update({
            'total_employees': total_employees,
            'total_departments': total_departments,
            'present_today': present_today,
            'pending_leaves': pending_leaves,
            'recent_leave_requests': LeaveRequest.objects.select_related('employee', 'leave_type').filter(status=LeaveRequestStatus.PENDING).order_by('-created_at')[:5],
            'recent_attendances': Attendance.objects.select_related('employee').filter(date=today).order_by('-clock_in_time')[:5],
            'chart_attendance_breakdown': {
                'labels': list(att_counts.keys()),
                'data': list(att_counts.values())
            },
            'chart_dept_distribution': {
                'labels': dept_labels,
                'data': dept_counts
            },
            'chart_attendance_trend': {
                'labels': trend_labels,
                'data': trend_counts
            },
        })

    elif user.role == User.Role.MANAGER:
        # --- MANAGER SCOPE ---
        subordinates = Employee.objects.filter(manager__user=user, employment_status=EmploymentStatus.ACTIVE)
        total_team = subordinates.count()

        subordinate_ids = list(subordinates.values_list('id', flat=True))
        if hasattr(user, 'employee_profile'):
            subordinate_ids.append(user.employee_profile.id)

        present_today = Attendance.objects.filter(
            date=today,
            employee_id__in=subordinate_ids,
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]
        ).count()

        pending_leaves = LeaveRequest.objects.filter(
            status=LeaveRequestStatus.PENDING,
            employee__manager__user=user
        ).exclude(employee__user=user).count()

        total_departments = Department.objects.filter(status=True).count()

        # Team Attendance Breakdown
        team_att_qs = Attendance.objects.filter(date=today, employee_id__in=subordinate_ids)
        att_counts = {
            'Present': team_att_qs.filter(status=AttendanceStatus.PRESENT).count(),
            'Late': team_att_qs.filter(status=AttendanceStatus.LATE).count(),
            'Half Day': team_att_qs.filter(status=AttendanceStatus.HALF_DAY).count(),
            'On Leave': team_att_qs.filter(status=AttendanceStatus.ON_LEAVE).count(),
            'Absent': team_att_qs.filter(status=AttendanceStatus.ABSENT).count(),
        }

        # Department distribution within team
        dept_qs = Department.objects.filter(status=True, employees__in=subordinates).annotate(
            emp_count=Count('employees', filter=Q(employees__in=subordinates))
        ).distinct()
        dept_labels = [dept.name for dept in dept_qs]
        dept_counts = [dept.emp_count for dept in dept_qs]

        # 7-Day Team Trend
        start_trend_date = today - timedelta(days=6)
        trend_dates = [(start_trend_date + timedelta(days=i)) for i in range(7)]
        trend_labels = [d.strftime('%a %d %b') for d in trend_dates]

        trend_qs = Attendance.objects.filter(
            date__gte=start_trend_date,
            date__lte=today,
            employee_id__in=subordinate_ids,
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]
        ).values('date').annotate(cnt=Count('id'))
        trend_map = {item['date']: item['cnt'] for item in trend_qs}
        trend_counts = [trend_map.get(d, 0) for d in trend_dates]

        context.update({
            'total_employees': total_team,
            'total_departments': total_departments,
            'present_today': present_today,
            'pending_leaves': pending_leaves,
            'recent_leave_requests': LeaveRequest.objects.select_related('employee', 'leave_type').filter(status=LeaveRequestStatus.PENDING, employee__manager__user=user).exclude(employee__user=user).order_by('-created_at')[:5],
            'recent_attendances': Attendance.objects.select_related('employee').filter(date=today, employee_id__in=subordinate_ids).order_by('-clock_in_time')[:5],
            'chart_attendance_breakdown': {
                'labels': list(att_counts.keys()),
                'data': list(att_counts.values())
            },
            'chart_dept_distribution': {
                'labels': dept_labels,
                'data': dept_counts
            },
            'chart_attendance_trend': {
                'labels': trend_labels,
                'data': trend_counts
            },
        })

    else:
        # --- EMPLOYEE SCOPE ---
        emp_profile = getattr(user, 'employee_profile', None)
        today_att = None
        leave_balances = []
        my_pending_leaves = 0
        my_recent_leaves = []
        my_recent_attendance = []

        if emp_profile:
            today_att = Attendance.objects.filter(employee=emp_profile, date=today).first()
            leave_balances = LeaveBalance.objects.select_related('leave_type').filter(employee=emp_profile, year=today.year)
            my_pending_leaves = LeaveRequest.objects.filter(employee=emp_profile, status=LeaveRequestStatus.PENDING).count()
            my_recent_leaves = LeaveRequest.objects.select_related('leave_type').filter(employee=emp_profile).order_by('-created_at')[:5]
            my_recent_attendance = Attendance.objects.filter(employee=emp_profile).order_by('-date')[:7]

        # For employee chart: 7-Day Working Hours Trend
        start_trend_date = today - timedelta(days=6)
        trend_dates = [(start_trend_date + timedelta(days=i)) for i in range(7)]
        trend_labels = [d.strftime('%a %d %b') for d in trend_dates]

        hours_map = {}
        if emp_profile:
            hours_qs = Attendance.objects.filter(
                employee=emp_profile,
                date__gte=start_trend_date,
                date__lte=today
            ).values('date', 'working_hours')
            hours_map = {item['date']: float(item['working_hours'] or 0.0) for item in hours_qs}

        trend_hours = [hours_map.get(d, 0.0) for d in trend_dates]

        balance_labels = [b.leave_type.code for b in leave_balances]
        balance_data = [float(b.remaining_days) for b in leave_balances]

        context.update({
            'today_attendance': today_att,
            'leave_balances': leave_balances,
            'pending_leaves': my_pending_leaves,
            'my_recent_leaves': my_recent_leaves,
            'my_recent_attendance': my_recent_attendance,
            'chart_attendance_breakdown': {
                'labels': balance_labels,
                'data': balance_data
            },
            'chart_dept_distribution': {
                'labels': [],
                'data': []
            },
            'chart_attendance_trend': {
                'labels': trend_labels,
                'data': trend_hours
            },
        })

    return render(request, 'dashboard/index.html', context)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('dashboard/', home_view, name='dashboard'),

    # Domain App Routes
    path('accounts/', include('apps.accounts.urls')),
    path('departments/', include('apps.departments.urls')),
    path('employees/', include('apps.employees.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('leaves/', include('apps.leaves.urls')),
    path('notifications/', include('apps.notifications.urls')),

    # OpenAPI Schema & Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
