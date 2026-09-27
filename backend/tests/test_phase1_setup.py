import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_custom_user_model_configured():
    """Verify that custom User model is properly registered and functional."""
    assert settings.AUTH_USER_MODEL == 'accounts.User'
    assert User.__name__ == 'User'


@pytest.mark.django_db
def test_user_creation():
    """Test user creation with roles."""
    user = User.objects.create_user(
        email='admin@eelms.com',
        password='SecurePassword123!',
        role=User.Role.ADMIN
    )
    assert user.email == 'admin@eelms.com'
    assert user.role == 'ADMIN'
    assert user.check_password('SecurePassword123!') is True


def test_installed_apps():
    """Ensure all required domain apps are registered."""
    expected_apps = [
        'apps.accounts',
        'apps.departments',
        'apps.employees',
        'apps.attendance',
        'apps.leaves',
        'apps.notifications',
        'apps.documents',
        'apps.reports',
        'apps.audit',
    ]
    for app in expected_apps:
        assert any(inst_app.startswith(app) for inst_app in settings.INSTALLED_APPS)
