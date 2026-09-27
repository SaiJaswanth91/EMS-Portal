import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.departments.models import Department, Designation
from apps.employees.models import Employee, EmploymentStatus, EmploymentType

User = get_user_model()


@pytest.fixture
def setup_rbac_users(db):
    """Fixture initializing role users and employee records."""
    dept_tech = Department.objects.create(name="Technology", code="TECH")
    dept_fin = Department.objects.create(name="Finance", code="FIN")

    # 1. Admin & HR Users
    admin_user = User.objects.create_superuser(email="admin_rbac@eelms.com", password="Password123!")
    hr_user = User.objects.create_user(email="hr_rbac@eelms.com", password="Password123!", role=User.Role.HR)

    # 2. Managers
    mgr_a_user = User.objects.create_user(email="mgr_a@eelms.com", password="Password123!", role=User.Role.MANAGER)
    mgr_b_user = User.objects.create_user(email="mgr_b@eelms.com", password="Password123!", role=User.Role.MANAGER)

    mgr_a = Employee.objects.create(user=mgr_a_user, first_name="Manager", last_name="A", email=mgr_a_user.email, department=dept_tech)
    mgr_b = Employee.objects.create(user=mgr_b_user, first_name="Manager", last_name="B", email=mgr_b_user.email, department=dept_fin)

    # 3. Regular Employees
    emp_a1_user = User.objects.create_user(email="emp_a1@eelms.com", password="Password123!", role=User.Role.EMPLOYEE)
    emp_b1_user = User.objects.create_user(email="emp_b1@eelms.com", password="Password123!", role=User.Role.EMPLOYEE)

    emp_a1 = Employee.objects.create(user=emp_a1_user, first_name="Emp", last_name="A1", email=emp_a1_user.email, department=dept_tech, manager=mgr_a)
    emp_b1 = Employee.objects.create(user=emp_b1_user, first_name="Emp", last_name="B1", email=emp_b1_user.email, department=dept_fin, manager=mgr_b)

    return {
        'admin': admin_user,
        'hr': hr_user,
        'mgr_a': mgr_a_user,
        'mgr_b': mgr_b_user,
        'emp_a1': emp_a1_user,
        'emp_b1': emp_b1_user,
        'emp_a1_obj': emp_a1,
        'emp_b1_obj': emp_b1,
        'dept_tech': dept_tech,
    }


@pytest.mark.django_db
def test_unauthenticated_user_redirected_to_login(client):
    """Verify that unauthenticated HTTP requests to protected views redirect to login."""
    protected_urls = [
        reverse('dashboard'),
        reverse('department_list'),
        reverse('employee_list'),
    ]
    for url in protected_urls:
        response = client.get(url)
        assert response.status_code == 302
        assert reverse('login') in response.url


@pytest.mark.django_db
def test_employee_role_cannot_create_department(client, setup_rbac_users):
    """Verify regular Employee receives 403 Forbidden when attempting department creation."""
    client.login(username=setup_rbac_users['emp_a1'].email, password='Password123!')
    url = reverse('department_create')
    
    response = client.post(url, {'name': 'Illegal Dept', 'code': 'ILL'})
    assert response.status_code == 403


@pytest.mark.django_db
def test_employee_role_cannot_create_employee(client, setup_rbac_users):
    """Verify regular Employee receives 403 Forbidden when attempting employee creation."""
    client.login(username=setup_rbac_users['emp_a1'].email, password='Password123!')
    url = reverse('employee_create')
    
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_employee_idor_cannot_view_other_employee_profile(client, setup_rbac_users):
    """Verify Object-Level IDOR Protection: Employee A cannot view Employee B's profile."""
    client.login(username=setup_rbac_users['emp_a1'].email, password='Password123!')
    emp_b_id = setup_rbac_users['emp_b1_obj'].pk
    url = reverse('employee_detail', kwargs={'pk': emp_b_id})
    
    response = client.get(url)
    assert response.status_code == 403  # Raised PermissionDenied


@pytest.mark.django_db
def test_employee_can_view_own_profile(client, setup_rbac_users):
    """Verify Employee A can view their own profile."""
    client.login(username=setup_rbac_users['emp_a1'].email, password='Password123!')
    emp_a_id = setup_rbac_users['emp_a1_obj'].pk
    url = reverse('employee_detail', kwargs={'pk': emp_a_id})
    
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_manager_idor_cannot_view_unrelated_team_employee(client, setup_rbac_users):
    """Verify Manager A cannot view Employee B (who belongs to Manager B's team)."""
    client.login(username=setup_rbac_users['mgr_a'].email, password='Password123!')
    emp_b_id = setup_rbac_users['emp_b1_obj'].pk
    url = reverse('employee_detail', kwargs={'pk': emp_b_id})
    
    response = client.get(url)
    assert response.status_code == 403  # Forbidden for cross-team employee access


@pytest.mark.django_db
def test_manager_can_view_subordinate_profile(client, setup_rbac_users):
    """Verify Manager A can view Employee A1 (direct subordinate)."""
    client.login(username=setup_rbac_users['mgr_a'].email, password='Password123!')
    emp_a_id = setup_rbac_users['emp_a1_obj'].pk
    url = reverse('employee_detail', kwargs={'pk': emp_a_id})
    
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_manager_cannot_edit_other_employee_profile(client, setup_rbac_users):
    """Verify Manager A cannot edit Employee A1 or Employee B1 profiles."""
    client.login(username=setup_rbac_users['mgr_a'].email, password='Password123!')
    emp_a_id = setup_rbac_users['emp_a1_obj'].pk
    url = reverse('employee_edit', kwargs={'pk': emp_a_id})
    
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_hr_full_access_to_management(client, setup_rbac_users):
    """Verify HR role has full access to creation views."""
    client.login(username=setup_rbac_users['hr'].email, password='Password123!')
    
    res_dept = client.get(reverse('department_create'))
    assert res_dept.status_code == 200

    res_emp = client.get(reverse('employee_create'))
    assert res_emp.status_code == 200
