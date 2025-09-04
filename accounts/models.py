from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending AbstractUser with role-based access
    This is configured as AUTH_USER_MODEL in settings.py
    """

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("host", "Host"),
        ("attendee", "Attendee"),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="attendee",
        help_text="User role determines access permissions",
    )

    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)

    class Meta:
        db_table = "auth_user"

    def __str__(self):
        return f"{self.username} ({self.role})"

    def is_admin(self):
        return self.role == "admin"

    def is_host(self):
        return self.role == "host"

    def is_attendee(self):
        return self.role == "attendee"
