from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from apps.accounts.mixins import RoleRequiredMixin
from apps.employees.models import Employee
from .models import LeaveType, LeavePolicy, LeaveBalance, LeaveRequest, LeaveRequestStatus
from .forms import LeaveTypeForm, LeaveApplyForm, LeaveApproveForm, LeaveRejectForm


class LeaveBalanceListView(LoginRequiredMixin, ListView):
    """View displaying leave balances for the logged-in employee."""
    model = LeaveBalance
    template_name = 'leaves/leave_balance_list.html'
    context_object_name = 'balances'

    def get_queryset(self):
        user = self.request.user
        year = timezone.now().year
        if hasattr(user, 'employee_profile'):
            return LeaveBalance.objects.select_related('leave_type').filter(employee=user.employee_profile, year=year)
        return LeaveBalance.objects.none()


class LeaveApplyView(LoginRequiredMixin, CreateView):
    """View for employees to submit a leave request."""
    model = LeaveRequest
    form_class = LeaveApplyForm
    template_name = 'leaves/leave_apply_form.html'
    success_url = reverse_lazy('leave_request_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'employee_profile'):
            kwargs['employee'] = self.request.user.employee_profile
        return kwargs

    def form_valid(self, form):
        if not hasattr(self.request.user, 'employee_profile'):
            messages.error(self.request, "Your account does not have an active Employee profile.")
            return redirect('leave_request_list')

        leave_request = form.save(commit=False)
        leave_request.employee = self.request.user.employee_profile
        leave_request.total_days = form.cleaned_data['total_days']
        leave_request.status = LeaveRequestStatus.PENDING
        leave_request.save()

        messages.success(
            self.request,
            f"Leave application for {leave_request.total_days} days submitted successfully! Status: Pending Manager Approval."
        )
        return redirect('leave_request_list')


class LeaveRequestListView(LoginRequiredMixin, ListView):
    """Role-aware list of leave requests."""
    model = LeaveRequest
    template_name = 'leaves/leave_request_list.html'
    context_object_name = 'leave_requests'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = LeaveRequest.objects.select_related('employee', 'leave_type', 'approved_by').order_by('-created_at')

        if user.role == 'EMPLOYEE':
            queryset = queryset.filter(employee__user=user)
        elif user.role == 'MANAGER':
            queryset = queryset.filter(Q(employee__user=user) | Q(employee__manager__user=user))

        status_filter = self.request.GET.get('status')
        type_filter = self.request.GET.get('type')
        search_query = self.request.GET.get('q')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if type_filter:
            queryset = queryset.filter(leave_type_id=type_filter)
        if search_query and user.role in ['ADMIN', 'HR', 'MANAGER']:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search_query) |
                Q(employee__last_name__icontains=search_query) |
                Q(employee__employee_id__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['leave_types'] = LeaveType.objects.filter(status=True)
        context['statuses'] = LeaveRequestStatus.choices
        context['status_filter'] = self.request.GET.get('status', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class LeaveRequestDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single Leave Request."""
    model = LeaveRequest
    template_name = 'leaves/leave_request_detail.html'
    context_object_name = 'leave_request'

    def get_object(self, queryset=None):
        req = super().get_object(queryset)
        user = self.request.user

        if user.is_superuser or user.role in ['ADMIN', 'HR']:
            return req
        elif user.role == 'MANAGER' and (req.employee.user == user or req.employee.is_managed_by(user)):
            return req
        elif req.employee.user == user:
            return req

        raise PermissionDenied("You do not have permission to view this leave request.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        req = self.object
        
        # Check if current user can approve/reject this request
        is_authorized_approver = (
            user.is_superuser or
            user.role in ['ADMIN', 'HR'] or
            (user.role == 'MANAGER' and req.employee.is_managed_by(user) and req.employee.user != user)
        )
        context['is_authorized_approver'] = is_authorized_approver
        context['approve_form'] = LeaveApproveForm()
        context['reject_form'] = LeaveRejectForm()
        return context


class PendingApprovalsView(RoleRequiredMixin, ListView):
    """Manager & HR dashboard listing pending leave approval requests."""
    allowed_roles = ['ADMIN', 'HR', 'MANAGER']
    model = LeaveRequest
    template_name = 'leaves/pending_approvals.html'
    context_object_name = 'pending_requests'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = LeaveRequest.objects.select_related('employee', 'leave_type').filter(status=LeaveRequestStatus.PENDING)

        if user.role == 'MANAGER':
            queryset = queryset.filter(employee__manager__user=user).exclude(employee__user=user)

        return queryset.order_by('created_at')


class LeaveApproveView(RoleRequiredMixin, View):
    """Atomic Leave Approval Handler with Row Locking (select_for_update)."""
    allowed_roles = ['ADMIN', 'HR', 'MANAGER']

    def post(self, request, pk):
        user = request.user
        
        with transaction.atomic():
            # 1. Lock LeaveRequest Row
            leave_req = get_object_or_404(
                LeaveRequest.objects.select_for_update(),
                pk=pk
            )

            # 2. Authorization Check
            if not (user.is_superuser or user.role in ['ADMIN', 'HR'] or leave_req.employee.is_managed_by(user)):
                raise PermissionDenied("You do not have permission to approve this leave request.")

            # 3. Check State
            if leave_req.status != LeaveRequestStatus.PENDING:
                messages.error(request, f"This leave request has already been processed (Current status: {leave_req.get_status_display()}).")
                return redirect('leave_request_detail', pk=pk)

            # 4. Lock LeaveBalance Row
            year = leave_req.start_date.year
            balance = LeaveBalance.objects.select_for_update().filter(
                employee=leave_req.employee,
                leave_type=leave_req.leave_type,
                year=year
            ).first()

            if not balance:
                messages.error(request, f"Leave balance record not found for {leave_req.employee.get_full_name()} in {year}.")
                return redirect('leave_request_detail', pk=pk)

            if leave_req.total_days > balance.remaining_days:
                messages.error(
                    request,
                    f"Approval failed: Insufficient remaining balance ({balance.remaining_days} days remaining vs {leave_req.total_days} requested)."
                )
                return redirect('leave_request_detail', pk=pk)

            # 5. Process Approval & Deduct Balance
            form = LeaveApproveForm(request.POST)
            comment = form.cleaned_data['manager_comment'] if form.is_valid() else ''

            balance.used_days += leave_req.total_days
            balance.save()  # Recalculates remaining_days

            leave_req.status = LeaveRequestStatus.APPROVED
            leave_req.approved_by = user
            leave_req.approved_at = timezone.now()
            leave_req.manager_comment = comment
            leave_req.save()

            messages.success(request, f"Leave request for {leave_req.employee.get_full_name()} has been APPROVED successfully!")
            return redirect('leave_request_detail', pk=pk)


class LeaveRejectView(RoleRequiredMixin, View):
    """Atomic Leave Rejection Handler with Mandatory Comment."""
    allowed_roles = ['ADMIN', 'HR', 'MANAGER']

    def post(self, request, pk):
        user = request.user
        
        form = LeaveRejectForm(request.POST)
        if not form.is_valid():
            comment_err = form.errors.get('manager_comment', ['Rejection reason is required.'])[0]
            messages.error(request, f"Rejection Failed: {comment_err}")
            return redirect('leave_request_detail', pk=pk)

        comment = form.cleaned_data['manager_comment']

        with transaction.atomic():
            # 1. Lock LeaveRequest Row
            leave_req = get_object_or_404(
                LeaveRequest.objects.select_for_update(),
                pk=pk
            )

            # 2. Authorization Check
            if not (user.is_superuser or user.role in ['ADMIN', 'HR'] or leave_req.employee.is_managed_by(user)):
                raise PermissionDenied("You do not have permission to reject this leave request.")

            # 3. Check State
            if leave_req.status != LeaveRequestStatus.PENDING:
                messages.error(request, f"This leave request has already been processed (Current status: {leave_req.get_status_display()}).")
                return redirect('leave_request_detail', pk=pk)

            # 4. Process Rejection (No balance change)
            leave_req.status = LeaveRequestStatus.REJECTED
            leave_req.approved_by = user
            leave_req.approved_at = timezone.now()
            leave_req.manager_comment = comment
            leave_req.save()

            messages.warning(request, f"Leave request for {leave_req.employee.get_full_name()} has been REJECTED.")
            return redirect('leave_request_detail', pk=pk)


class LeaveTypeListView(RoleRequiredMixin, ListView):
    """HR & Admin view to manage Leave Types."""
    allowed_roles = ['ADMIN', 'HR']
    model = LeaveType
    template_name = 'leaves/leave_type_list.html'
    context_object_name = 'leave_types'


class LeaveTypeCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ['ADMIN', 'HR']
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = 'leaves/leave_type_form.html'
    success_url = reverse_lazy('leave_type_list')

    def form_valid(self, form):
        messages.success(self.request, f"Leave type '{form.instance.name}' created successfully!")
        return super().form_valid(form)


class LeaveTypeUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ['ADMIN', 'HR']
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = 'leaves/leave_type_form.html'
    success_url = reverse_lazy('leave_type_list')

    def form_valid(self, form):
        messages.success(self.request, f"Leave type '{form.instance.name}' updated successfully!")
        return super().form_valid(form)
