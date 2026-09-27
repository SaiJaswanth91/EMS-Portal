from django import forms
from .models import Department, Designation


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'department_head', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Engineering'}),
            'code': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'e.g. TECH'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Department purpose and goals...'}),
            'department_head': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper().strip()
        instance_id = self.instance.pk if self.instance else None
        
        if Department.objects.filter(code=code).exclude(pk=instance_id).exists():
            raise forms.ValidationError("A department with this code already exists. Department codes must be unique.")
        return code


class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designation
        fields = ['name', 'department', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Software Developer'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Key responsibilities...'}),
        }
