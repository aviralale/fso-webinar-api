from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Registration


@receiver(post_save, sender=Registration)
def send_registration_confirmation(sender, instance, created, **kwargs):
    """
    Send email confirmation when registration payment is successful
    """
    if not created and instance.payment_status == "success":
        subject = f"Registration Confirmed: {instance.webinar.title}"
        message = f"""
        Dear {instance.user.get_full_name()},
        
        Your registration for "{instance.webinar.title}" has been confirmed!
        
        Webinar Details:
        - Date & Time: {instance.webinar.start_time}
        - Duration: {instance.webinar.duration_minutes} minutes
        - Host: {instance.webinar.host.get_full_name()}
        
        Thank you for registering!
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.user.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Handle email sending errors gracefully
