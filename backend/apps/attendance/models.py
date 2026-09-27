from datetime import datetime, time, timedelta
from django.db import models
from django.utils import timezone
from apps.employees.models import Employee


class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', 'Present'
    ABSENT = 'ABSENT', 'Absent'
    LATE = 'LATE', 'Late'
    HALF_DAY = 'HALF_DAY', 'Half Day'
    ON_LEAVE = 'ON_LEAVE', 'On Leave'
    HOLIDAY = 'HOLIDAY', 'Holiday'


class Attendance(models.Model):
    """Attendance entity recording daily clock-in/out and working hours."""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Employee'
    )
    date = models.DateField('Attendance Date', default=timezone.now, db_index=True)
    clock_in_time = models.TimeField('Clock In Time', null=True, blank=True)
    clock_out_time = models.TimeField('Clock Out Time', null=True, blank=True)
    working_hours = models.DecimalField(
        'Working Hours',
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Server-calculated total working hours"
    )
    status = models.CharField(
        'Attendance Status',
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT
    )
    notes = models.TextField('Notes / Remarks', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-date', '-clock_in_time']
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} [{self.get_status_display()}]"

    def calculate_hours_and_status(self, shift_start_time=time(9, 30), grace_minutes=15):
        """
        Server-side calculation of working hours and status based on clock-in and clock-out.
        - Clock-in after shift_start + grace_minutes -> LATE.
        - Working hours < 4.0 -> HALF_DAY.
        """
        if self.clock_in_time:
            # Check for late clock-in
            grace_cutoff = (
                datetime.combine(self.date, shift_start_time) + timedelta(minutes=grace_minutes)
            ).time()

            if self.clock_in_time > grace_cutoff and self.status == AttendanceStatus.PRESENT:
                self.status = AttendanceStatus.LATE

        if self.clock_in_time and self.clock_out_time:
            dt_in = datetime.combine(self.date, self.clock_in_time)
            dt_out = datetime.combine(self.date, self.clock_out_time)

            if dt_out > dt_in:
                delta = dt_out - dt_in
                total_hours = round(delta.total_seconds() / 3600.0, 2)
                self.working_hours = total_hours

                # Half-day rule if less than 4 hours worked
                if total_hours < 4.0 and self.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]:
                    self.status = AttendanceStatus.HALF_DAY

    def save(self, *args, **kwargs):
        self.calculate_hours_and_status()
        super().save(*args, **kwargs)
