from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_full_name', 'email', 'department', 'designation', 'manager', 'employment_status', 'joining_date')
    list_filter = ('department', 'employment_status', 'employment_type', 'gender')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')
    readonly_fields = ('employee_id', 'created_at', 'updated_at')
    ordering = ('employee_id',)
