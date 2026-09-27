from django.contrib import admin
from .models import Department, Designation


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department_head', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'created_at')
    list_filter = ('department',)
    search_fields = ('name', 'department__name', 'department__code')
    ordering = ('name',)
