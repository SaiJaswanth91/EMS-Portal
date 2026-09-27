from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
from apps.employees.models import Employee, EmploymentType, EmploymentStatus


class LeaveRequestStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Approval'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    CANCELLED = 'CANCELLED', 'Cancelled'


class LeaveType(models.Model):
    """Leave Category definition (e.g., Casual, Sick, Earned)."""
    code = models.CharField('Leave Code', max_length=20, unique=True, db_index=True)
    name = models.CharField('Leave Type Name', max_length=100)
    is_paid = models.BooleanField('Paid Leave', default=True)
    max_days_per_year = models.IntegerField('Max Quota / Year', default=12)
    requires_document = models.BooleanField('Requires Document Attachment', default=False)
    status = models.BooleanField('Active Status', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Leave Type'
        verbose_name_plural = 'Leave Types'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        super().clean()
        if self.code:
            self.code = self.code.upper().strip()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class LeavePolicy(models.Model):
    """Policy matrix assigning default leave quotas based on employment type."""
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='policies')
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)
    allocated_days = models.DecimalField(max_digits=5, decimal_places=1, default=12.0)

    class Meta:
        verbose_name = 'Leave Policy'
        verbose_name_plural = 'Leave Policies'
        unique_together = ('leave_type', 'employment_type')

    def __str__(self):
        return f"{self.leave_type.name} - {self.get_employment_type_display()} ({self.allocated_days} days)"


class LeaveBalance(models.Model):
    """Employee Leave Balance record for a specific calendar year."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='balances')
    year = models.IntegerField('Calendar Year', default=2026, db_index=True)
    allocated_days = models.DecimalField('Allocated Days', max_digits=5, decimal_places=1, default=0.0)
    used_days = models.DecimalField('Used Days', max_digits=5, decimal_places=1, default=0.0)
    remaining_days = models.DecimalField('Remaining Days', max_digits=5, decimal_places=1, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'
        unique_together = ('employee', 'leave_type', 'year')
        ordering = ['employee', 'leave_type']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.code} ({self.remaining_days} remaining)"

    def recalculate_remaining(self):
        """Calculate remaining leave days."""
        self.remaining_days = max(Decimal('0.0'), self.allocated_days - self.used_days)

    def save(self, *args, **kwargs):
        self.recalculate_remaining()
        super().save(*args, **kwargs)


class LeaveRequest(models.Model):
    """Individual Leave Application submitted by an employee."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name='requests')
    start_date = models.DateField('Start Date', db_index=True)
    end_date = models.DateField('End Date', db_index=True)
    total_days = models.DecimalField('Total Requested Days', max_digits=4, decimal_places=1)
    reason = models.TextField('Reason for Leave')
    
    status = models.CharField(
        'Request Status',
        max_length=20,
        choices=LeaveRequestStatus.choices,
        default=LeaveRequestStatus.PENDING,
        db_index=True
    )
    manager_comment = models.TextField('Manager / HR Comment', blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leave_requests'
    )
    approved_at = models.DateTimeField('Approved / Rejected At', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.code} ({self.start_date} to {self.end_date}) [{self.status}]"

    @staticmethod
    def calculate_requested_days(start_date, end_date):
        """Calculate number of calendar working days between start_date and end_date."""
        if not start_date or not end_date or start_date > end_date:
            return Decimal('0.0')
        delta = (end_date - start_date).days + 1
        return Decimal(str(delta))

    def clean(self):
        super().clean()
        # 1. Date range validation
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({'end_date': "End date cannot be earlier than start date."})

        # 2. Employee Active Status check (Safely handling unassigned employee during Form clean)
        try:
            if self.employee and self.employee.employment_status != EmploymentStatus.ACTIVE:
                raise ValidationError("Leave applications can only be submitted by active employees.")
        except ObjectDoesNotExist:
            pass

        # 3. Overlap check for PENDING / APPROVED requests
        try:
            if self.employee and self.start_date and self.end_date:
                overlapping_query = LeaveRequest.objects.filter(
                    employee=self.employee,
                    status__in=[LeaveRequestStatus.PENDING, LeaveRequestStatus.APPROVED]
                ).filter(
                    start_date__lte=self.end_date,
                    end_date__gte=self.start_date
                )
                if self.pk:
                    overlapping_query = overlapping_query.exclude(pk=self.pk)

                if overlapping_query.exists():
                    raise ValidationError("You already have an active or pending leave request overlapping with these dates.")
        except ObjectDoesNotExist:
            pass

        # 4. Leave Balance check
        try:
            if self.employee and self.leave_type and self.start_date and self.end_date and self.status == LeaveRequestStatus.PENDING:
                calc_days = self.calculate_requested_days(self.start_date, self.end_date)
                year = self.start_date.year
                balance = LeaveBalance.objects.filter(employee=self.employee, leave_type=self.leave_type, year=year).first()

                if not balance:
                    raise ValidationError(f"No leave balance allocated for {self.leave_type.name} in {year}.")
                if calc_days > balance.remaining_days:
                    raise ValidationError(f"Insufficient leave balance. Requested: {calc_days} days, Remaining: {balance.remaining_days} days.")
        except ObjectDoesNotExist:
            pass
