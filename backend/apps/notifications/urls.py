from django.urls import path
from .views import NotificationListView, MarkNotificationReadView, MarkAllNotificationsReadView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification_mark_read'),
    path('mark-all-read/', MarkAllNotificationsReadView.as_view(), name='notification_mark_all_read'),
]
