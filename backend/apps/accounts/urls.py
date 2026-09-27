from django.urls import path
from .views import (
    EELMSLoginView, EELMSLogoutView, ProfileView,
    EELMSPasswordResetView, EELMSPasswordResetDoneView,
    EELMSPasswordResetConfirmView, EELMSPasswordResetCompleteView
)

urlpatterns = [
    path('login/', EELMSLoginView.as_view(), name='login'),
    path('logout/', EELMSLogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Password Reset URLs
    path('password-reset/', EELMSPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', EELMSPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', EELMSPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', EELMSPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
