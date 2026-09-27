from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Department(models.Model):
    """Department entity representing organizational units."""
    name = models.CharField('Department Name', max_length=100)
    code = models.CharField('Department Code', max_length=10, unique=True, db_index=True, help_text="Unique short code (e.g., TECH, HR, FIN)")
    description = models.TextField('Description', blank=True)
    department_head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        verbose_name='Department Head'
    )
    status = models.BooleanField('Active Status', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
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


class Designation(models.Model):
    """Designation entity representing job roles within departments."""
    name = models.CharField('Designation Title', max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='designations',
        null=True,
        blank=True,
        verbose_name='Department'
    )
    description = models.TextField('Job Description / Responsibilities', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Designation'
        verbose_name_plural = 'Designations'
        ordering = ['name']
        unique_together = ('name', 'department')

    def __str__(self):
        dept_str = f" - {self.department.code}" if self.department else ""
        return f"{self.name}{dept_str}"
