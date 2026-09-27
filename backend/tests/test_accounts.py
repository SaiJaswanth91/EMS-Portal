import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from apps.accounts.decorators import role_required

User = get_user_model()


@pytest.mark.django_db
def test_create_user_and_superuser():
    """Test CustomUserManager create_user and create_superuser methods."""
    user = User.objects.create_user(email='testuser@eelms.com', password='Password123!', role=User.Role.EMPLOYEE)
    assert user.email == 'testuser@eelms.com'
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.role == User.Role.EMPLOYEE

    admin = User.objects.create_superuser(email='testadmin@eelms.com', password='Password123!')
    assert admin.email == 'testadmin@eelms.com'
    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.role == User.Role.ADMIN


@pytest.mark.django_db
def test_valid_user_login(client):
    """Test successful user login."""
    User.objects.create_user(email='user@eelms.com', password='SecurePassword123!')
    url = reverse('login')
    response = client.post(url, {'username': 'user@eelms.com', 'password': 'SecurePassword123!'})
    assert response.status_code == 302  # Redirects to dashboard upon success
    assert response.url == reverse('dashboard')


@pytest.mark.django_db
def test_invalid_password_login_failure(client):
    """Test login failure with invalid password."""
    User.objects.create_user(email='user@eelms.com', password='SecurePassword123!')
    url = reverse('login')
    response = client.post(url, {'username': 'user@eelms.com', 'password': 'WrongPassword!'})
    assert response.status_code == 200  # Renders login page with error
    assert '_auth_user_id' not in client.session


@pytest.mark.django_db
def test_inactive_user_login_blocked(client):
    """Test that inactive users cannot authenticate."""
    user = User.objects.create_user(email='inactive@eelms.com', password='SecurePassword123!')
    user.is_active = False
    user.save()

    url = reverse('login')
    response = client.post(url, {'username': 'inactive@eelms.com', 'password': 'SecurePassword123!'})
    assert response.status_code == 200
    assert '_auth_user_id' not in client.session


@pytest.mark.django_db
def test_user_logout(client):
    """Test user logout and session clearing."""
    user = User.objects.create_user(email='user@eelms.com', password='SecurePassword123!')
    client.login(username='user@eelms.com', password='SecurePassword123!')
    
    url = reverse('logout')
    response = client.post(url)
    assert response.status_code == 302
    assert '_auth_user_id' not in client.session


@pytest.mark.django_db
def test_role_required_decorator_permission_denied(rf):
    """Test that role_required raises PermissionDenied for unauthorized roles."""
    user = User.objects.create_user(email='emp@eelms.com', password='Password123!', role=User.Role.EMPLOYEE)
    
    @role_required(['ADMIN', 'HR'])
    def protected_view(request):
        return "Allowed"

    request = rf.get('/protected/')
    request.user = user

    with pytest.raises(PermissionDenied):
        protected_view(request)


@pytest.mark.django_db
def test_password_reset_page_loads(client):
    """Test password reset form page rendering."""
    url = reverse('password_reset')
    response = client.get(url)
    assert response.status_code == 200
    assert 'Reset Password' in response.content.decode()
