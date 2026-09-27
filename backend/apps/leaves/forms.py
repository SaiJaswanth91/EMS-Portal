from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from .models import LeaveType, LeaveBalance, LeaveRequest, LeaveRequestStatus


class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ['code', 'name', 'is_paid', 'max_days_per_year', 'requires_document', 'status']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'e.g. CASUAL'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Casual Leave'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_days_per_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'requires_document': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper().strip()
        instance_id = self.instance.pk if self.instance else None
        if LeaveType.objects.filter(code=code).exclude(pk=instance_id).exists():
            raise forms.ValidationError("A leave type with this code already exists.")
        return code


class LeaveApplyForm(forms.ModelForm):
    """Form used by Employees to apply for leave."""
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Provide reason for leave application...'}),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        if self.employee:
            self.fields['leave_type'].queryset = LeaveType.objects.filter(status=True)

    def clean(self):
        cleaned_data = super().clean()
        leave_type = cleaned_data.get('leave_type')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if not self.employee:
            raise ValidationError("An active employee profile is required to apply for leave.")

        if start_date and end_date:
            if start_date > end_date:
                self.add_error('end_date', "End date cannot be earlier than start date.")
                return cleaned_data

            total_days = LeaveRequest.calculate_requested_days(start_date, end_date)

            overlapping = LeaveRequest.objects.filter(
                employee=self.employee,
                status__in=[LeaveRequestStatus.PENDING, LeaveRequestStatus.APPROVED]
            ).filter(
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if overlapping.exists():
                raise ValidationError("You already have a pending or approved leave request overlapping with these dates.")

            year = start_date.year
            balance = LeaveBalance.objects.filter(employee=self.employee, leave_type=leave_type, year=year).first()
            if not balance:
                raise ValidationError(f"You do not have a leave balance allocated for {leave_type.name} in {year}.")

            if total_days > balance.remaining_days:
                raise ValidationError(f"Insufficient leave balance. You requested {total_days} days, but only have {balance.remaining_days} days remaining.")

            cleaned_data['total_days'] = total_days

        return cleaned_data


class LeaveApproveForm(forms.Form):
    """Form used by Managers to approve leave requests."""
    manager_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional approval remarks...'}),
        label='Approval Remarks'
    )


class LeaveRejectForm(forms.Form):
    """Form used by Managers to reject leave requests (Mandatory rejection reason)."""
    manager_comment = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Mandatory rejection reason...'}),
        label='Rejection Reason *'
    )

    def clean_manager_comment(self):
        comment = self.cleaned_data.get('manager_comment', '').strip()
        if not comment:
            raise forms.ValidationError("A rejection reason is mandatory when rejecting a leave request.")
        return comment
