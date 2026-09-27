from decimal import Decimal
from datetime import date
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.departments.models import Department
from apps.employees.models import Employee, EmploymentStatus
from apps.leaves.models import LeaveType, LeaveBalance, LeaveRequest, LeaveRequestStatus

User = get_user_model()


@pytest.fixture
def setup_leave_data(db):
    dept = Department.objects.create(name="Engineering", code="TECH")
    u = User.objects.create_user(email="leave_user@eelms.com", password="Password123!", role=User.Role.EMPLOYEE)
    emp = Employee.objects.create(user=u, first_name="Leave", last_name="Tester", email=u.email, department=dept)
    
    casual_type = LeaveType.objects.create(code="CASUAL", name="Casual Leave", max_days_per_year=12, status=True)
    
    balance = LeaveBalance.objects.create(
        employee=emp,
        leave_type=casual_type,
        year=2026,
        allocated_days=Decimal('12.0'),
        used_days=Decimal('0.0'),
        remaining_days=Decimal('12.0')
    )
    return u, emp, casual_type, balance


@pytest.mark.django_db
def test_successful_leave_application(client, setup_leave_data):
    """Test successful submission of a leave application."""
    user, emp, casual_type, balance = setup_leave_data
    client.login(username=user.email, password="Password123!")

    url = reverse('leave_apply')
    response = client.post(url, {
        'leave_type': casual_type.id,
        'start_date': '2026-06-01',
        'end_date': '2026-06-03',
        'reason': 'Personal work at home',
    })
    assert response.status_code == 302
    assert response.url == reverse('leave_request_list')

    req = LeaveRequest.objects.get(employee=emp, leave_type=casual_type)
    assert req.total_days == Decimal('3.0')
    assert req.status == LeaveRequestStatus.PENDING


@pytest.mark.django_db
def test_invalid_date_range_validation(client, setup_leave_data):
    """Test that end_date earlier than start_date fails form validation."""
    user, emp, casual_type, balance = setup_leave_data
    client.login(username=user.email, password="Password123!")

    url = reverse('leave_apply')
    response = client.post(url, {
        'leave_type': casual_type.id,
        'start_date': '2026-06-05',
        'end_date': '2026-06-01',
        'reason': 'Invalid dates',
    })
    assert response.status_code == 200
    assert 'end_date' in response.context['form'].errors


@pytest.mark.django_db
def test_overlapping_leave_validation(client, setup_leave_data):
    """Test that overlapping leave applications for the same employee fail."""
    user, emp, casual_type, balance = setup_leave_data
    client.login(username=user.email, password="Password123!")

    # Existing pending request June 1 - June 5
    LeaveRequest.objects.create(
        employee=emp,
        leave_type=casual_type,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 5),
        total_days=Decimal('5.0'),
        reason="First leave",
        status=LeaveRequestStatus.PENDING
    )

    url = reverse('leave_apply')
    response = client.post(url, {
        'leave_type': casual_type.id,
        'start_date': '2026-06-03',
        'end_date': '2026-06-07',
        'reason': 'Overlapping leave',
    })
    assert response.status_code == 200
    assert "overlapping" in str(response.context['form'].errors).lower()


@pytest.mark.django_db
def test_insufficient_leave_balance_validation(client, setup_leave_data):
    """Test that applying for more days than available remaining balance fails."""
    user, emp, casual_type, balance = setup_leave_data
    client.login(username=user.email, password="Password123!")

    # Set balance remaining to only 2 days
    balance.allocated_days = Decimal('2.0')
    balance.save()

    url = reverse('leave_apply')
    response = client.post(url, {
        'leave_type': casual_type.id,
        'start_date': '2026-06-01',
        'end_date': '2026-06-05', # Requested 5 days
        'reason': 'Exceeding balance',
    })
    assert response.status_code == 200
    assert "insufficient" in str(response.context['form'].errors).lower()
