from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email_task(self, recipient_email, subject, message_body):
    """
    Asynchronous Celery task to send email notifications.
    Retries up to 3 times if SMTP delivery fails.
    """
    try:
        send_mail(
            subject=subject,
            message=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return f"Email sent successfully to {recipient_email}"
    except Exception as exc:
        self.retry(exc=exc)
