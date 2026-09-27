from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum, Avg
from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.mixins import RoleRequiredMixin
from apps.employees.models import Employee
from apps.departments.models import Department
from .models import Attendance, AttendanceStatus
from .forms import ClockInForm, ClockOutForm


class AttendanceListView(LoginRequiredMixin, ListView):
    """Attendance log directory with role-aware querysets and filters."""
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user
        queryset = Attendance.objects.select_related('employee', 'employee__user', 'employee__department', 'employee__designation').order_by('-date', '-clock_in_time')

        # Object-level RBAC filtering
        if user.role == 'EMPLOYEE':
            queryset = queryset.filter(employee__user=user)
        elif user.role == 'MANAGER':
            queryset = queryset.filter(Q(employee__user=user) | Q(employee__manager__user=user))

        # Filters
        search_query = self.request.GET.get('q')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status_filter = self.request.GET.get('status')
        dept_filter = self.request.GET.get('department')

        if search_query:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search_query) |
                Q(employee__last_name__icontains=search_query) |
                Q(employee__employee_id__icontains=search_query)
            )

        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if dept_filter:
            queryset = queryset.filter(employee__department_id=dept_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        # Check today's attendance for logged in employee
        today_attendance = None
        if hasattr(user, 'employee_profile'):
            today_attendance = Attendance.objects.filter(employee=user.employee_profile, date=today).first()

        context['today_attendance'] = today_attendance
        context['today_date'] = today
        context['departments'] = Department.objects.filter(status=True)
        context['statuses'] = AttendanceStatus.choices
        context['clock_in_form'] = ClockInForm()
        context['clock_out_form'] = ClockOutForm()

        # Context filter values
        context['search_query'] = self.request.GET.get('q', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['dept_filter'] = self.request.GET.get('department', '')

        return context


class ClockInView(LoginRequiredMixin, View):
    """Server-validated clock-in handler."""

    def post(self, request):
        if not hasattr(request.user, 'employee_profile'):
            messages.error(request, "Your account does not have an associated Employee profile.")
            return redirect('attendance_list')

        employee = request.user.employee_profile
        today = timezone.now().date()
        now_time = timezone.now().time()

        # Rule 1: Cannot clock in twice on the same day
        existing_record = Attendance.objects.filter(employee=employee, date=today).first()
        if existing_record and existing_record.clock_in_time:
            messages.warning(request, f"You have already clocked in today at {existing_record.clock_in_time.strftime('%I:%M %p')}.")
            return redirect('attendance_list')

        form = ClockInForm(request.POST)
        notes = form.cleaned_data['notes'] if form.is_valid() else ''

        if existing_record:
            existing_record.clock_in_time = now_time
            if notes:
                existing_record.notes = f"{existing_record.notes}\nClock-in: {notes}".strip()
            existing_record.save()
            record = existing_record
        else:
            record = Attendance.objects.create(
                employee=employee,
                date=today,
                clock_in_time=now_time,
                notes=f"Clock-in: {notes}".strip() if notes else '',
                status=AttendanceStatus.PRESENT
            )

        messages.success(request, f"Successfully clocked in at {now_time.strftime('%I:%M %p')}! Status: {record.get_status_display()}")
        return redirect('attendance_list')


class ClockOutView(LoginRequiredMixin, View):
    """Server-validated clock-out handler."""

    def post(self, request):
        if not hasattr(request.user, 'employee_profile'):
            messages.error(request, "Your account does not have an associated Employee profile.")
            return redirect('attendance_list')

        employee = request.user.employee_profile
        today = timezone.now().date()
        now_time = timezone.now().time()

        record = Attendance.objects.filter(employee=employee, date=today).first()

        # Rule 2: Cannot clock out without clocking in first
        if not record or not record.clock_in_time:
            messages.error(request, "You must clock in first before clocking out!")
            return redirect('attendance_list')

        # Rule 3: Cannot clock out twice on the same day
        if record.clock_out_time:
            messages.warning(request, f"You have already clocked out today at {record.clock_out_time.strftime('%I:%M %p')}.")
            return redirect('attendance_list')

        form = ClockOutForm(request.POST)
        notes = form.cleaned_data['notes'] if form.is_valid() else ''

        record.clock_out_time = now_time
        if notes:
            record.notes = f"{record.notes}\nClock-out: {notes}".strip()
        record.save()  # Triggers calculate_hours_and_status() in model

        messages.success(
            request,
            f"Successfully clocked out at {now_time.strftime('%I:%M %p')}! Total Hours: {record.working_hours} hrs."
        )
        return redirect('attendance_list')


class TeamAttendanceView(RoleRequiredMixin, ListView):
    """Manager & HR view monitoring today's team attendance status."""
    allowed_roles = ['ADMIN', 'HR', 'MANAGER']
    model = Attendance
    template_name = 'attendance/team_attendance.html'
    context_object_name = 'attendances'

    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        queryset = Attendance.objects.select_related('employee', 'employee__department', 'employee__designation').filter(date=today)

        if user.role == 'MANAGER':
            queryset = queryset.filter(employee__manager__user=user)

        return queryset.order_by('employee__first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        if user.role == 'MANAGER':
            team_employees = Employee.objects.filter(manager__user=user, employment_status='ACTIVE')
        else:
            team_employees = Employee.objects.filter(employment_status='ACTIVE')

        context['today_date'] = today
        context['total_team'] = team_employees.count()
        context['present_count'] = context['attendances'].filter(status__in=['PRESENT', 'LATE']).count()
        context['absent_count'] = context['total_team'] - context['present_count']
        return context
