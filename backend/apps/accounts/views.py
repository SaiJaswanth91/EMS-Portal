from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, 
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import UpdateView, TemplateView
from django.contrib.auth import get_user_model
from .forms import UserLoginForm, CustomPasswordResetForm, CustomSetPasswordForm, UserProfileForm

User = get_user_model()


class EELMSLoginView(LoginView):
    """Custom Login view enforcing email-based authentication with Bootstrap styling."""
    template_name = 'registration/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().get_full_name()}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email address or password. Please try again.")
        return super().form_invalid(form)


class EELMSLogoutView(LogoutView):
    """Custom Logout View."""
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, UpdateView):
    """User profile detail and edit view."""
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)


class EELMSPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')


class EELMSPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class EELMSPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('password_reset_complete')


class EELMSPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'
