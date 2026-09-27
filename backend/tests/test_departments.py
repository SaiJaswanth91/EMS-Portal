import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.departments.models import Department, Designation

User = get_user_model()


@pytest.mark.django_db
def test_create_department():
    """Test Department creation and automatic uppercase code cleaning."""
    dept = Department.objects.create(name="Research & Development", code="rnd", description="R&D Lab")
    assert dept.code == "RND"
    assert str(dept) == "Research & Development (RND)"
    assert dept.status is True


@pytest.mark.django_db
def test_create_designation():
    """Test Designation model creation linked to a department."""
    dept = Department.objects.create(name="Engineering", code="TECH")
    desig = Designation.objects.create(name="DevOps Engineer", department=dept, description="Cloud infrastructure")
    assert desig.name == "DevOps Engineer"
    assert desig.department == dept
    assert "TECH" in str(desig)


@pytest.mark.django_db
def test_department_create_view_hr_admin(client):
    """Test that HR user can create a new department."""
    hr_user = User.objects.create_user(email='hr_test@eelms.com', password='Password123!', role=User.Role.HR)
    client.login(username='hr_test@eelms.com', password='Password123!')

    url = reverse('department_create')
    response = client.post(url, {
        'name': 'Customer Support',
        'code': 'SUPP',
        'description': 'Helpline and support team',
        'status': True,
    })
    assert response.status_code == 302
    assert Department.objects.filter(code='SUPP').exists()


@pytest.mark.django_db
def test_department_create_view_employee_forbidden(client):
    """Test that regular Employee receives 403 Forbidden when attempting to create a department."""
    emp_user = User.objects.create_user(email='emp_test@eelms.com', password='Password123!', role=User.Role.EMPLOYEE)
    client.login(username='emp_test@eelms.com', password='Password123!')

    url = reverse('department_create')
    response = client.post(url, {
        'name': 'Unauthorized Dept',
        'code': 'UNAUTH',
    })
    assert response.status_code == 403
    assert not Department.objects.filter(code='UNAUTH').exists()


@pytest.mark.django_db
def test_department_toggle_status(client):
    """Test toggling department active/inactive status."""
    admin_user = User.objects.create_superuser(email='admin_test@eelms.com', password='Password123!')
    client.login(username='admin_test@eelms.com', password='Password123!')

    dept = Department.objects.create(name="Operations", code="OPS", status=True)
    url = reverse('department_toggle_status', kwargs={'pk': dept.pk})
    
    response = client.post(url)
    assert response.status_code == 302
    dept.refresh_from_db()
    assert dept.status is False
