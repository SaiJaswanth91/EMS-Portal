from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from apps.accounts.mixins import RoleRequiredMixin
from apps.departments.models import Department
from .models import Employee, EmploymentStatus, EmploymentType
from .forms import EmployeeCreateForm, EmployeeUpdateForm, EmployeeSelfUpdateForm

User = get_user_model()


class EmployeeListView(LoginRequiredMixin, ListView):
    """List employees with optimized select_related, filters, and search."""
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Employee.objects.select_related('user', 'department', 'designation', 'manager').order_by('employee_id')

        # Object-level security / RBAC filtering
        if user.role == User.Role.MANAGER:
            # Managers can view themselves and their direct subordinates
            queryset = queryset.filter(Q(user=user) | Q(manager__user=user))
        elif user.role == User.Role.EMPLOYEE:
            # Regular employees see active employees
            queryset = queryset.filter(employment_status=EmploymentStatus.ACTIVE)

        search_query = self.request.GET.get('q')
        dept_filter = self.request.GET.get('department')
        status_filter = self.request.GET.get('status')
        type_filter = self.request.GET.get('type')

        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )

        if dept_filter:
            queryset = queryset.filter(department_id=dept_filter)

        if status_filter:
            queryset = queryset.filter(employment_status=status_filter)

        if type_filter:
            queryset = queryset.filter(employment_type=type_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(status=True)
        context['statuses'] = EmploymentStatus.choices
        context['types'] = EmploymentType.choices
        context['search_query'] = self.request.GET.get('q', '')
        context['dept_filter'] = self.request.GET.get('department', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['total_employees'] = Employee.objects.count()
        context['active_employees'] = Employee.objects.filter(employment_status=EmploymentStatus.ACTIVE).count()
        return context


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of single Employee record with object-level permission check."""
    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

    def get_queryset(self):
        return Employee.objects.select_related('user', 'department', 'designation', 'manager', 'manager__user')

    def get_object(self, queryset=None):
        emp = super().get_object(queryset)
        user = self.request.user

        # Object-level authorization check: IDOR protection
        if user.is_superuser or user.role in [User.Role.ADMIN, User.Role.HR]:
            return emp
        elif user.role == User.Role.MANAGER and (emp.user == user or emp.is_managed_by(user)):
            return emp
        elif emp.user == user:
            return emp

        # Explicitly deny cross-tenant or unauthorized user access
        raise PermissionDenied("You do not have permission to view this private employee profile.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subordinates'] = self.object.subordinates.select_related('department', 'designation').all()
        return context


class EmployeeCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ['ADMIN', 'HR']
    model = Employee
    form_class = EmployeeCreateForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employee_list')

    @transaction.atomic
    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['user_password']
        role = form.cleaned_data['user_role']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']

        # 1. Create User Account
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            is_verified=True
        )

        # 2. Attach User to Employee Profile
        employee = form.save(commit=False)
        employee.user = user
        employee.save()

        messages.success(self.request, f"Employee '{employee.get_full_name()}' created successfully with ID {employee.employee_id}!")
        return redirect('employee_list')


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employee_list')

    def get_form_class(self):
        user = self.request.user
        if user.role in [User.Role.ADMIN, User.Role.HR]:
            return EmployeeUpdateForm
        return EmployeeSelfUpdateForm

    def get_object(self, queryset=None):
        emp = super().get_object(queryset)
        user = self.request.user

        if user.is_superuser or user.role in [User.Role.ADMIN, User.Role.HR]:
            return emp
        elif emp.user == user:
            return emp

        # Manager or regular Employee attempting to edit another user's profile raises 403
        raise PermissionDenied("You do not have permission to edit another employee's profile.")

    def form_valid(self, form):
        employee = form.save()
        user = employee.user
        user.first_name = employee.first_name
        user.last_name = employee.last_name
        user.email = employee.email
        user.save()

        messages.success(self.request, f"Employee profile '{employee.get_full_name()}' updated successfully!")
        return redirect('employee_detail', pk=employee.pk)
