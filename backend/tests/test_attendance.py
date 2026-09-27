from datetime import time, date, timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.departments.models import Department
from apps.employees.models import Employee
from apps.attendance.models import Attendance, AttendanceStatus

User = get_user_model()


@pytest.fixture
def setup_attendance_employee(db):
    dept = Department.objects.create(name="Engineering", code="TECH")
    u = User.objects.create_user(email="att_user@eelms.com", password="Password123!", role=User.Role.EMPLOYEE)
    emp = Employee.objects.create(user=u, first_name="John", last_name="Att", email=u.email, department=dept)
    return u, emp


@pytest.mark.django_db
def test_clock_in_success(client, setup_attendance_employee):
    """Test successful clock-in action."""
    user, emp = setup_attendance_employee
    client.login(username=user.email, password="Password123!")

    url = reverse('clock_in')
    response = client.post(url, {'notes': 'Office clock-in'})
    assert response.status_code == 302

    today = timezone.now().date()
    att = Attendance.objects.get(employee=emp, date=today)
    assert att.clock_in_time is not None
    assert att.clock_out_time is None
    assert att.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]


@pytest.mark.django_db
def test_duplicate_clock_in_blocked(client, setup_attendance_employee):
    """Test that clocking in twice on the same day does not duplicate records."""
    user, emp = setup_attendance_employee
    client.login(username=user.email, password="Password123!")

    url = reverse('clock_in')
    client.post(url, {'notes': 'First clock in'})
    client.post(url, {'notes': 'Second clock in attempt'})

    today = timezone.now().date()
    assert Attendance.objects.filter(employee=emp, date=today).count() == 1


@pytest.mark.django_db
def test_clock_out_without_clock_in_blocked(client, setup_attendance_employee):
    """Test that clocking out without clocking in first is blocked."""
    user, emp = setup_attendance_employee
    client.login(username=user.email, password="Password123!")

    url = reverse('clock_out')
    response = client.post(url)
    assert response.status_code == 302

    today = timezone.now().date()
    assert not Attendance.objects.filter(employee=emp, date=today).exists()


@pytest.mark.django_db
def test_working_hours_calculation_and_half_day_rule():
    """Test working hours calculation and half-day status rule."""
    dept = Department.objects.create(name="HR", code="HR")
    u = User.objects.create_user(email="halfday@eelms.com", password="Password123!")
    emp = Employee.objects.create(user=u, first_name="Half", last_name="Day", email=u.email, department=dept)

    # 3 hours worked -> HALF_DAY
    att = Attendance.objects.create(
        employee=emp,
        date=date(2026, 5, 10),
        clock_in_time=time(9, 0),
        clock_out_time=time(12, 0),
        status=AttendanceStatus.PRESENT
    )
    assert att.working_hours == 3.00
    assert att.status == AttendanceStatus.HALF_DAY

    # 8 hours worked -> PRESENT
    att2 = Attendance.objects.create(
        employee=emp,
        date=date(2026, 5, 11),
        clock_in_time=time(9, 0),
        clock_out_time=time(17, 0),
        status=AttendanceStatus.PRESENT
    )
    assert att2.working_hours == 8.00
    assert att2.status == AttendanceStatus.PRESENT


@pytest.mark.django_db
def test_late_clock_in_rule():
    """Test that clocking in after 09:45 AM sets status to LATE."""
    dept = Department.objects.create(name="Sales", code="SLS")
    u = User.objects.create_user(email="lateuser@eelms.com", password="Password123!")
    emp = Employee.objects.create(user=u, first_name="Late", last_name="Guy", email=u.email, department=dept)

    att = Attendance.objects.create(
        employee=emp,
        date=date(2026, 5, 12),
        clock_in_time=time(10, 15),
        status=AttendanceStatus.PRESENT
    )
    assert att.status == AttendanceStatus.LATE
