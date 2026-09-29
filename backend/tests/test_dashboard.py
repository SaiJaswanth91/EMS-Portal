import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.employees.models import Employee, EmploymentStatus, EmploymentType
from apps.departments.models import Department, Designation
from apps.attendance.models import Attendance, AttendanceStatus
from apps.leaves.models import LeaveType, LeaveRequest, LeaveRequestStatus, LeaveBalance


@pytest.mark.django_db
class TestDynamicDashboard:
    """Test suite for role-aware dynamic dashboard metrics and access controls."""

    def test_unauthenticated_dashboard_redirect(self, client):
        """Unauthenticated requests must redirect to login."""
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302
        assert reverse('login') in response.url

    def test_admin_dashboard_metrics(self, client, db):
        """ADMIN user sees organization-wide metrics."""
        admin_user = User.objects.create_user(
            email="admin_dash@example.com",
            password="Password123!",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )

        dept = Department.objects.create(name="Engineering", code="ENG", status=True)
        desg = Designation.objects.create(name="Senior Engineer", department=dept)

        # Create active employee
        emp_user = User.objects.create_user(email="emp_dash1@example.com", password="Password123!", role=User.Role.EMPLOYEE)
        emp = Employee.objects.create(
            user=emp_user,
            first_name="Alice",
            last_name="Smith",
            email=emp_user.email,
            department=dept,
            designation=desg,
            employment_status=EmploymentStatus.ACTIVE
        )

        today = timezone.now().date()
        Attendance.objects.create(employee=emp, date=today, status=AttendanceStatus.PRESENT)

        leave_type = LeaveType.objects.create(code="CASUAL", name="Casual Leave")
        LeaveRequest.objects.create(
            employee=emp,
            leave_type=leave_type,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=2),
            total_days=2,
            reason="Vacation",
            status=LeaveRequestStatus.PENDING
        )

        client.force_login(admin_user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200

        # Verify context metrics
        assert response.context['total_employees'] == 1
        assert response.context['total_departments'] == 1
        assert response.context['present_today'] == 1
        assert response.context['pending_leaves'] == 1

        # Verify chart structure
        assert 'chart_attendance_breakdown' in response.context
        assert 'chart_dept_distribution' in response.context
        assert 'chart_attendance_trend' in response.context
        assert response.context['chart_dept_distribution']['data'] == [1]

    def test_manager_dashboard_scoping(self, client, db):
        """MANAGER sees team metrics and direct subordinate pending approvals."""
        mgr_user = User.objects.create_user(email="mgr_dash@example.com", password="Password123!", role=User.Role.MANAGER)
        dept = Department.objects.create(name="Operations", code="OPS", status=True)

        mgr_emp = Employee.objects.create(
            user=mgr_user,
            first_name="Bob",
            last_name="Manager",
            email=mgr_user.email,
            department=dept,
            employment_status=EmploymentStatus.ACTIVE
        )

        # Subordinate
        sub_user = User.objects.create_user(email="sub_dash@example.com", password="Password123!", role=User.Role.EMPLOYEE)
        sub_emp = Employee.objects.create(
            user=sub_user,
            first_name="Charlie",
            last_name="Sub",
            email=sub_user.email,
            department=dept,
            manager=mgr_emp,
            employment_status=EmploymentStatus.ACTIVE
        )

        # Other employee not managed by Bob
        other_user = User.objects.create_user(email="other_dash@example.com", password="Password123!", role=User.Role.EMPLOYEE)
        other_emp = Employee.objects.create(
            user=other_user,
            first_name="Dave",
            last_name="Other",
            email=other_user.email,
            department=dept,
            employment_status=EmploymentStatus.ACTIVE
        )

        leave_type = LeaveType.objects.create(code="SICK", name="Sick Leave")
        # Pending leave for team member
        LeaveRequest.objects.create(
            employee=sub_emp,
            leave_type=leave_type,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            total_days=1,
            reason="Fever",
            status=LeaveRequestStatus.PENDING
        )
        # Pending leave for non-team member
        LeaveRequest.objects.create(
            employee=other_emp,
            leave_type=leave_type,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            total_days=1,
            reason="Personal",
            status=LeaveRequestStatus.PENDING
        )

        client.force_login(mgr_user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200

        # Manager should only count direct subordinates (1) and team pending leaves (1)
        assert response.context['total_employees'] == 1
        assert response.context['pending_leaves'] == 1

    def test_employee_dashboard(self, client, db):
        """EMPLOYEE sees personal status and leave balances."""
        emp_user = User.objects.create_user(email="emp_personal@example.com", password="Password123!", role=User.Role.EMPLOYEE)
        dept = Department.objects.create(name="HR Dept", code="HRD", status=True)

        emp = Employee.objects.create(
            user=emp_user,
            first_name="Eva",
            last_name="Green",
            email=emp_user.email,
            department=dept,
            employment_status=EmploymentStatus.ACTIVE
        )

        leave_type = LeaveType.objects.create(code="EARNED", name="Earned Leave")
        LeaveBalance.objects.create(
            employee=emp,
            leave_type=leave_type,
            year=timezone.now().year,
            allocated_days=15,
            used_days=3,
            remaining_days=12
        )

        client.force_login(emp_user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200

        assert 'leave_balances' in response.context
        assert len(response.context['leave_balances']) == 1
        assert response.context['leave_balances'][0].remaining_days == 12

    def test_empty_database_dashboard(self, client, db):
        """Dashboard renders safely even if database has zero employees, departments, or records."""
        admin_user = User.objects.create_user(
            email="admin_empty@example.com",
            password="Password123!",
            role=User.Role.ADMIN
        )

        client.force_login(admin_user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert response.context['total_employees'] == 0
        assert response.context['total_departments'] == 0
        assert response.context['present_today'] == 0
        assert response.context['pending_leaves'] == 0
