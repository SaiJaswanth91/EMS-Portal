from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'clock_in_time', 'clock_out_time', 'working_hours', 'status')
    list_filter = ('status', 'date', 'employee__department')
    search_fields = ('employee__employee_id', 'employee__first_name', 'employee__last_name', 'employee__email')
    ordering = ('-date', '-clock_in_time')
