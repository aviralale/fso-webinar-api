from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User


class Webinar(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="webinar_images/", blank=True, null=True)
    start_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    host = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "host"},
        related_name="hosted_webinars",
    )
    link = models.URLField(blank=True, null=True)
    platform = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return self.title

    @property
    def is_full(self):
        return (
            self.registrations.filter(payment_status="success").count() >= self.capacity
        )

    @property
    def registered_count(self):
        return self.registrations.filter(payment_status="success").count()


class Registration(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    # For authenticated users
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="registrations",
        null=True,  # Allow null for anonymous registrations
        blank=True,
    )

    # For anonymous/guest users
    guest_email = models.EmailField(null=True, blank=True)
    guest_name = models.CharField(max_length=200, null=True, blank=True)
    guest_phone = models.CharField(max_length=20, null=True, blank=True)

    webinar = models.ForeignKey(
        Webinar, on_delete=models.CASCADE, related_name="registrations"
    )
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    # Email reminder tracking
    reminder_24h_sent = models.BooleanField(default=False)
    reminder_1h_sent = models.BooleanField(default=False)
    starting_notification_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Remove the unique constraint on user+webinar since user can be null
        # Add a custom constraint to handle both authenticated and anonymous users
        ordering = ["-registered_at"]

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.webinar.title}"
        else:
            return f"{self.guest_email} - {self.webinar.title}"

    @property
    def attendee_name(self):
        """Get the attendee name regardless of whether it's a user or guest"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        else:
            return self.guest_name

    @property
    def attendee_email(self):
        """Get the attendee email regardless of whether it's a user or guest"""
        if self.user:
            return self.user.email
        else:
            return self.guest_email

    def clean(self):
        """Custom validation to ensure either user or guest details are provided"""
        from django.core.exceptions import ValidationError

        if not self.user and not self.guest_email:
            raise ValidationError("Either user or guest_email must be provided")

        if self.user and self.guest_email:
            raise ValidationError("Cannot have both user and guest details")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
