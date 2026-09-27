from django.db import models
from django.conf import settings


class NotificationType(models.TextChoices):
    LEAVE_APPLIED = 'LEAVE_APPLIED', 'Leave Applied'
    LEAVE_APPROVED = 'LEAVE_APPROVED', 'Leave Approved'
    LEAVE_REJECTED = 'LEAVE_REJECTED', 'Leave Rejected'
    ATTENDANCE_REMINDER = 'ATTENDANCE_REMINDER', 'Attendance Reminder'
    DOCUMENT_EXPIRING = 'DOCUMENT_EXPIRING', 'Document Expiring'
    SYSTEM = 'SYSTEM', 'System Alert'


class Notification(models.Model):
    """Notification entity storing in-app alerts for users."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='User'
    )
    title = models.CharField('Notification Title', max_length=200)
    message = models.TextField('Notification Message')
    notification_type = models.CharField(
        'Type',
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        db_index=True
    )
    is_read = models.BooleanField('Read Status', default=False, db_index=True)
    link_url = models.CharField('Target Link URL', max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title} [{self.get_notification_type_display()}]"

    @classmethod
    def send_notification(cls, user, title, message, notification_type=NotificationType.SYSTEM, link_url=''):
        """Utility method to create an in-app notification record."""
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link_url=link_url
        )
