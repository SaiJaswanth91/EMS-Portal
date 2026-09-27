from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(AccessMixin):
    """
    CBV Mixin to verify that the current user has an authorized role.
    Usage:
        class EmployeeListView(RoleRequiredMixin, ListView):
            allowed_roles = ['ADMIN', 'HR', 'MANAGER']
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.is_superuser or request.user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("You do not have permission to view this page.")
