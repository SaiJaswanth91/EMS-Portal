from decimal import Decimal
from datetime import date
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.departments.models import Department
from apps.employees.models import Employee
from apps.leaves.models import LeaveType, LeaveBalance, LeaveRequest, LeaveRequestStatus

User = get_user_model()


@pytest.fixture
def setup_approval_data(db):
    dept = Department.objects.create(name="Engineering", code="TECH")
    
    # Manager User & Profile
    u_mgr = User.objects.create_user(email="mgr_appr@eelms.com", password="Password123!", role=User.Role.MANAGER)
    mgr_emp = Employee.objects.create(user=u_mgr, first_name="Manager", last_name="Lead", email=u_mgr.email, department=dept)

    # Subordinate Employee User & Profile
    u_sub = User.objects.create_user(email="sub_appr@eelms.com", password="Password123!", role=User.Role.EMPLOYEE)
    sub_emp = Employee.objects.create(user=u_sub, first_name="Sub", last_name="Staff", email=u_sub.email, department=dept, manager=mgr_emp)

    # Other Unauthorized Employee
    u_other = User.objects.create_user(email="other_appr@eelms.com", password="Password123!", role=User.Role.EMPLOYEE)

    # Leave Type & Balance
    casual_type = LeaveType.objects.create(code="CASUAL", name="Casual Leave", max_days_per_year=12, status=True)
    balance = LeaveBalance.objects.create(
        employee=sub_emp,
        leave_type=casual_type,
        year=2026,
        allocated_days=Decimal('12.0'),
        used_days=Decimal('0.0'),
        remaining_days=Decimal('12.0')
    )

    # Pending Leave Request
    leave_req = LeaveRequest.objects.create(
        employee=sub_emp,
        leave_type=casual_type,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 3),
        total_days=Decimal('3.0'),
        reason="Vacation request",
        status=LeaveRequestStatus.PENDING
    )

    return {
        'u_mgr': u_mgr,
        'u_sub': u_sub,
        'u_other': u_other,
        'mgr_emp': mgr_emp,
        'sub_emp': sub_emp,
        'casual_type': casual_type,
        'balance': balance,
        'leave_req': leave_req,
    }


@pytest.mark.django_db
def test_manager_leave_approval_updates_status_and_balance(client, setup_approval_data):
    """Test that manager approval atomically updates status and deducts leave balance."""
    data = setup_approval_data
    client.login(username=data['u_mgr'].email, password="Password123!")

    url = reverse('leave_approve', kwargs={'pk': data['leave_req'].pk})
    response = client.post(url, {'manager_comment': 'Approved by manager'})
    assert response.status_code == 302

    # Verify LeaveRequest Status
    data['leave_req'].refresh_from_db()
    assert data['leave_req'].status == LeaveRequestStatus.APPROVED
    assert data['leave_req'].approved_by == data['u_mgr']
    assert data['leave_req'].manager_comment == 'Approved by manager'

    # Verify LeaveBalance deduction
    data['balance'].refresh_from_db()
    assert data['balance'].used_days == Decimal('3.0')
    assert data['balance'].remaining_days == Decimal('9.0')


@pytest.mark.django_db
def test_manager_leave_rejection_requires_comment(client, setup_approval_data):
    """Test that manager rejection requires mandatory rejection reason."""
    data = setup_approval_data
    client.login(username=data['u_mgr'].email, password="Password123!")

    url = reverse('leave_reject', kwargs={'pk': data['leave_req'].pk})
    
    # 1. Reject without reason -> fails
    response_fail = client.post(url, {'manager_comment': ''})
    assert response_fail.status_code == 302
    data['leave_req'].refresh_from_db()
    assert data['leave_req'].status == LeaveRequestStatus.PENDING

    # 2. Reject with mandatory reason -> succeeds
    response_succ = client.post(url, {'manager_comment': 'Project deadline conflicting.'})
    assert response_succ.status_code == 302
    data['leave_req'].refresh_from_db()
    assert data['leave_req'].status == LeaveRequestStatus.REJECTED
    assert data['leave_req'].manager_comment == 'Project deadline conflicting.'

    # Balance remains untouched
    data['balance'].refresh_from_db()
    assert data['balance'].used_days == Decimal('0.0')


@pytest.mark.django_db
def test_unauthorized_user_cannot_approve_leave(client, setup_approval_data):
    """Test that an unauthorized regular employee receives 403 Forbidden when attempting approval."""
    data = setup_approval_data
    client.login(username=data['u_other'].email, password="Password123!")

    url = reverse('leave_approve', kwargs={'pk': data['leave_req'].pk})
    response = client.post(url, {'manager_comment': 'Unauthorized approval'})
    assert response.status_code == 403

    data['leave_req'].refresh_from_db()
    assert data['leave_req'].status == LeaveRequestStatus.PENDING
