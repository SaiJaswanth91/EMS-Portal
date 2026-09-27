from .models import Notification


def notification_context(request):
    """Context processor providing unread_notification_count and recent_notifications to all templates."""
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
        return {
            'unread_notification_count': unread_notifications.count(),
            'recent_unread_notifications': unread_notifications[:5],
        }
    return {
        'unread_notification_count': 0,
        'recent_unread_notifications': [],
    }
