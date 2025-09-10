from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

# Celery beat schedule for automatic email sending
app.conf.beat_schedule = {
    "send-24h-reminders": {
        "task": "webinars.tasks.send_webinar_reminders",
        "schedule": 3600.0,  # Run every hour
    },
    "send-1h-reminders": {
        "task": "webinars.tasks.send_one_hour_reminders",
        "schedule": 300.0,  # Run every 5 minutes
    },
    "send-starting-notifications": {
        "task": "webinars.tasks.send_webinar_starting_notifications",
        "schedule": 300.0,  # Run every 5 minutes
    },
}

app.conf.timezone = "UTC"
