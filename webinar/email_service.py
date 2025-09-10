from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class WebinarEmailService:
    @staticmethod
    def send_registration_confirmation(registration):
        """Send email confirmation when user registers for a webinar"""
        try:
            subject = f"Registration Confirmed: {registration.webinar.title}"

            # Get attendee details (works for both authenticated and anonymous users)
            attendee_name = registration.attendee_name
            attendee_email = registration.attendee_email

            # Prepare context for email template
            context = {
                "user_name": attendee_name,
                "attendee_email": attendee_email,
                "webinar_title": registration.webinar.title,
                "webinar_description": registration.webinar.description,
                "start_time": registration.webinar.start_time,
                "duration": registration.webinar.duration_minutes,
                "host_name": registration.webinar.host.get_full_name(),
                "webinar_link": registration.webinar.link,
                "platform": registration.webinar.platform,
                "price": registration.webinar.price,
                "registration_date": registration.registered_at,
                "registration_id": registration.id,
                "is_guest": not bool(registration.user),
            }

            # Render email templates
            html_message = render_to_string(
                "emails/registration_confirmation.html", context
            )
            text_message = render_to_string(
                "emails/registration_confirmation.txt", context
            )

            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[attendee_email],
                fail_silently=False,
            )

            logger.info(f"Registration confirmation email sent to {attendee_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send registration confirmation email: {str(e)}")
            return False

    @staticmethod
    def send_webinar_reminder(registration, reminder_type="24h"):
        """Send reminder email before webinar"""
        try:
            attendee_name = registration.attendee_name
            attendee_email = registration.attendee_email

            if reminder_type == "24h":
                subject = f"Reminder: {registration.webinar.title} starts tomorrow!"
                template_prefix = "24h_reminder"
            else:  # 1h reminder
                subject = f"Starting Soon: {registration.webinar.title} in 1 hour!"
                template_prefix = "1h_reminder"

            context = {
                "user_name": attendee_name,
                "attendee_email": attendee_email,
                "webinar_title": registration.webinar.title,
                "webinar_description": registration.webinar.description,
                "start_time": registration.webinar.start_time,
                "duration": registration.webinar.duration_minutes,
                "host_name": registration.webinar.host.get_full_name(),
                "webinar_link": registration.webinar.link,
                "platform": registration.webinar.platform,
                "reminder_type": reminder_type,
                "registration_id": registration.id,
                "is_guest": not bool(registration.user),
            }

            html_message = render_to_string(f"emails/{template_prefix}.html", context)
            text_message = render_to_string(f"emails/{template_prefix}.txt", context)

            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[attendee_email],
                fail_silently=False,
            )

            logger.info(f"{reminder_type} reminder email sent to {attendee_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send {reminder_type} reminder email: {str(e)}")
            return False

    @staticmethod
    def send_webinar_starting_notification(registration):
        """Send notification when webinar is starting"""
        try:
            attendee_name = registration.attendee_name
            attendee_email = registration.attendee_email

            subject = f"Join Now: {registration.webinar.title} is starting!"

            context = {
                "user_name": attendee_name,
                "attendee_email": attendee_email,
                "webinar_title": registration.webinar.title,
                "host_name": registration.webinar.host.get_full_name(),
                "webinar_link": registration.webinar.link,
                "platform": registration.webinar.platform,
                "start_time": registration.webinar.start_time,
                "registration_id": registration.id,
                "is_guest": not bool(registration.user),
            }

            html_message = render_to_string("emails/webinar_starting.html", context)
            text_message = render_to_string("emails/webinar_starting.txt", context)

            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[attendee_email],
                fail_silently=False,
            )

            logger.info(f"Webinar starting notification sent to {attendee_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send webinar starting notification: {str(e)}")
            return False
