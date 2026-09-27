import re
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.departments.models import Department, Designation


class EmploymentType(models.TextChoices):
    FULL_TIME = 'FULL_TIME', 'Full-Time'
    PART_TIME = 'PART_TIME', 'Part-Time'
    CONTRACT = 'CONTRACT', 'Contract'
    INTERN = 'INTERN', 'Intern'


class EmploymentStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    ON_LEAVE = 'ON_LEAVE', 'On Leave'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    RESIGNED = 'RESIGNED', 'Resigned'
    TERMINATED = 'TERMINATED', 'Terminated'


class Gender(models.TextChoices):
    MALE = 'MALE', 'Male'
    FEMALE = 'FEMALE', 'Female'
    OTHER = 'OTHER', 'Other'


def validate_profile_photo(image):
    """Validate profile photo file size (max 2MB) and extensions."""
    file_size = image.file.size
    limit_mb = 2.0
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Maximum allowed file size is {limit_mb} MB.")


class Employee(models.Model):
    """Core Employee Entity storing corporate and personal data."""
    employee_id = models.CharField(
        'Employee ID',
        max_length=30,
        unique=True,
        db_index=True,
        editable=False,
        help_text="Auto-generated unique ID (e.g. EMP-TECH-0001)"
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name='User Account'
    )
    first_name = models.CharField('First Name', max_length=50)
    last_name = models.CharField('Last Name', max_length=50)
    email = models.EmailField('Work Email', unique=True)
    phone = models.CharField('Phone Number', max_length=20, blank=True)
    dob = models.DateField('Date of Birth', null=True, blank=True)
    gender = models.CharField('Gender', max_length=10, choices=Gender.choices, default=Gender.MALE)
    address = models.TextField('Address', blank=True)
    
    joining_date = models.DateField('Joining Date', null=True, blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='Department'
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name='Designation'
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name='Reporting Manager'
    )
    
    employment_type = models.CharField(
        'Employment Type',
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME
    )
    employment_status = models.CharField(
        'Employment Status',
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE
    )
    profile_photo = models.ImageField(
        'Profile Photo',
        upload_to='profile_photos/',
        null=True,
        blank=True,
        validators=[validate_profile_photo]
    )
    emergency_contact = models.CharField('Emergency Contact Person', max_length=100, blank=True)
    emergency_phone = models.CharField('Emergency Phone', max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def is_managed_by(self, user):
        """Return True if specified user is this employee's reporting manager or Admin/HR."""
        if user.is_superuser or user.role in ['ADMIN', 'HR']:
            return True
        return self.manager is not None and self.manager.user == user

    @classmethod
    def generate_next_employee_id(cls, department_code):
        """
        Concurrency-safe Employee ID generator based on department code.
        Format: EMP-{DEPT_CODE}-{SEQUENCE:04d} (e.g. EMP-TECH-0001)
        Uses database transaction to avoid race conditions.
        """
        dept_code = department_code.upper().strip()
        prefix = f"EMP-{dept_code}-"

        with transaction.atomic():
            latest_emp = (
                cls.objects.filter(employee_id__startswith=prefix)
                .order_by('-employee_id')
                .select_for_update()
                .first()
            )

            if latest_emp:
                match = re.search(r'(\d+)$', latest_emp.employee_id)
                if match:
                    next_seq = int(match.group(1)) + 1
                else:
                    next_seq = 1
            else:
                next_seq = 1

            return f"{prefix}{next_seq:04d}"

    def save(self, *args, **kwargs):
        if not self.employee_id and self.department:
            self.employee_id = self.generate_next_employee_id(self.department.code)
        super().save(*args, **kwargs)
