from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """View displaying user's notifications with pagination."""
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class MarkNotificationReadView(LoginRequiredMixin, View):
    """Mark a single notification as read."""

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        
        if notification.link_url:
            return redirect(notification.link_url)
        return redirect('notification_list')


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Mark all unread notifications for the current user as read."""

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('notification_list')
