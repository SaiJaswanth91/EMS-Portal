import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.departments.models import Department, Designation
from apps.employees.models import Employee, EmploymentStatus, EmploymentType, Gender

User = get_user_model()


@pytest.mark.django_db
def test_employee_id_auto_generation():
    """Test sequential and concurrency-safe Employee ID generation format."""
    dept = Department.objects.create(name="Engineering", code="TECH")
    u1 = User.objects.create_user(email="dev1@eelms.com", password="Password123!")
    u2 = User.objects.create_user(email="dev2@eelms.com", password="Password123!")

    emp1 = Employee.objects.create(
        user=u1, first_name="Dev", last_name="One", email=u1.email, department=dept
    )
    assert emp1.employee_id == "EMP-TECH-0001"

    emp2 = Employee.objects.create(
        user=u2, first_name="Dev", last_name="Two", email=u2.email, department=dept
    )
    assert emp2.employee_id == "EMP-TECH-0002"


@pytest.mark.django_db
def test_manager_subordinate_relationship():
    """Test reporting manager relationship assignment."""
    dept = Department.objects.create(name="Finance", code="FIN")
    u_mgr = User.objects.create_user(email="fin_lead@eelms.com", password="Password123!", role=User.Role.MANAGER)
    u_sub = User.objects.create_user(email="acc1@eelms.com", password="Password123!", role=User.Role.EMPLOYEE)

    mgr = Employee.objects.create(user=u_mgr, first_name="Lead", last_name="Finance", email=u_mgr.email, department=dept)
    sub = Employee.objects.create(user=u_sub, first_name="Staff", last_name="Accountant", email=u_sub.email, department=dept, manager=mgr)

    assert sub.manager == mgr
    assert list(mgr.subordinates.all()) == [sub]


@pytest.mark.django_db
def test_employee_create_view_hr(client):
    """Test creating an employee via HR dashboard form."""
    hr_user = User.objects.create_user(email='hr_admin@eelms.com', password='Password123!', role=User.Role.HR)
    client.login(username='hr_admin@eelms.com', password='Password123!')

    dept = Department.objects.create(name="Human Resources", code="HR")
    url = reverse('employee_create')

    response = client.post(url, {
        'first_name': 'New',
        'last_name': 'Recruit',
        'email': 'new_recruit@eelms.com',
        'user_password': 'Password123!',
        'user_role': User.Role.EMPLOYEE,
        'department': dept.id,
        'gender': Gender.MALE,
        'employment_type': EmploymentType.FULL_TIME,
        'employment_status': EmploymentStatus.ACTIVE,
    })

    assert response.status_code == 302
    created_emp = Employee.objects.get(email='new_recruit@eelms.com')
    assert created_emp.employee_id == "EMP-HR-0001"
    assert created_emp.user.email == 'new_recruit@eelms.com'


@pytest.mark.django_db
def test_employee_create_forbidden_for_regular_employee(client):
    """Test that a regular employee cannot access employee creation endpoint."""
    emp_user = User.objects.create_user(email='staff@eelms.com', password='Password123!', role=User.Role.EMPLOYEE)
    client.login(username='staff@eelms.com', password='Password123!')

    url = reverse('employee_create')
    response = client.get(url)
    assert response.status_code == 403
