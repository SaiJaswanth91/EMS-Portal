from django import forms
from django.contrib.auth import get_user_model
from .models import Employee, EmploymentType, EmploymentStatus, Gender

User = get_user_model()


class EmployeeCreateForm(forms.ModelForm):
    """Form used by Admin & HR to create a new Employee and user account simultaneously."""
    user_password = forms.CharField(
        label='Initial Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        help_text='Employee will use this password to log in.'
    )
    user_role = forms.ChoiceField(
        label='User Role',
        choices=User.Role.choices,
        initial=User.Role.EMPLOYEE,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'dob', 'gender',
            'joining_date', 'department', 'designation', 'manager',
            'employment_type', 'employment_status', 'profile_photo',
            'address', 'emergency_contact', 'emergency_phone'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doe'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'john.doe@company.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 555 0192'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user account with this email address already exists.")
        return email


class EmployeeUpdateForm(forms.ModelForm):
    """Form used by HR & Admin to update existing Employee records."""
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'dob', 'gender',
            'joining_date', 'department', 'designation', 'manager',
            'employment_type', 'employment_status', 'profile_photo',
            'address', 'emergency_contact', 'emergency_phone'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EmployeeSelfUpdateForm(forms.ModelForm):
    """Form used by regular employees to edit their personal contact details."""
    class Meta:
        model = Employee
        fields = ['phone', 'address', 'profile_photo', 'emergency_contact', 'emergency_phone']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
