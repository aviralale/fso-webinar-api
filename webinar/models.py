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

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="registrations"
    )
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

    class Meta:
        unique_together = ["user", "webinar"]
        ordering = ["-registered_at"]

    def __str__(self):
        return f"{self.user.username} - {self.webinar.title}"
