from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Registration, Webinar
from .email_service import WebinarEmailService


@shared_task
def send_webinar_reminders():
    """Send 24-hour reminder emails for upcoming webinars"""
    tomorrow = timezone.now() + timedelta(days=1)
    start_of_tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_tomorrow = start_of_tomorrow + timedelta(days=1)

    # Get webinars starting tomorrow
    tomorrow_webinars = Webinar.objects.filter(
        start_time__gte=start_of_tomorrow, start_time__lt=end_of_tomorrow
    )

    sent_count = 0
    for webinar in tomorrow_webinars:
        registrations = Registration.objects.filter(
            webinar=webinar, payment_status="success"
        )

        for registration in registrations:
            if WebinarEmailService.send_webinar_reminder(registration, "24h"):
                sent_count += 1

    return f"Sent {sent_count} 24-hour reminder emails"


@shared_task
def send_one_hour_reminders():
    """Send 1-hour reminder emails for upcoming webinars"""
    one_hour_later = timezone.now() + timedelta(hours=1)

    # Get webinars starting in approximately 1 hour (within 10-minute window)
    webinars = Webinar.objects.filter(
        start_time__gte=one_hour_later - timedelta(minutes=5),
        start_time__lte=one_hour_later + timedelta(minutes=5),
    )

    sent_count = 0
    for webinar in webinars:
        registrations = Registration.objects.filter(
            webinar=webinar, payment_status="success"
        )

        for registration in registrations:
            if WebinarEmailService.send_webinar_reminder(registration, "1h"):
                sent_count += 1

    return f"Sent {sent_count} 1-hour reminder emails"


@shared_task
def send_webinar_starting_notifications():
    """Send notifications for webinars that are starting now"""
    now = timezone.now()

    # Get webinars starting within the next 10 minutes
    starting_webinars = Webinar.objects.filter(
        start_time__gte=now - timedelta(minutes=5),
        start_time__lte=now + timedelta(minutes=10),
    )

    sent_count = 0
    for webinar in starting_webinars:
        registrations = Registration.objects.filter(
            webinar=webinar, payment_status="success"
        )

        for registration in registrations:
            if WebinarEmailService.send_webinar_starting_notification(registration):
                sent_count += 1

    return f"Sent {sent_count} webinar starting notifications"
