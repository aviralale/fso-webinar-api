from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from webinar.models import Webinar, Registration


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "role", "is_active"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["username", "email", "first_name", "last_name"]

    fieldsets = BaseUserAdmin.fieldsets + (("Role Information", {"fields": ("role",)}),)

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role Information", {"fields": ("role",)}),
    )


@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "host",
        "start_time",
        "duration_minutes",
        "capacity",
        "price",
        "registered_count",
    ]
    list_filter = ["start_time", "host", "price"]
    search_fields = ["title", "description", "host__username"]
    readonly_fields = ["created_at", "updated_at", "registered_count"]

    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "image")}),
        ("Schedule", {"fields": ("start_time", "duration_minutes")}),
        ("Capacity & Pricing", {"fields": ("capacity", "price")}),
        ("Assignment", {"fields": ("host",)}),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at", "registered_count"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("host")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "host":
            kwargs["queryset"] = User.objects.filter(role="host")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "webinar",
        "payment_status",
        "registered_at",
        "razorpay_payment_id",
    ]
    list_filter = ["payment_status", "registered_at", "webinar"]
    search_fields = [
        "user__username",
        "user__email",
        "webinar__title",
        "razorpay_payment_id",
        "razorpay_order_id",
    ]
    readonly_fields = ["registered_at"]

    fieldsets = (
        ("Registration Info", {"fields": ("user", "webinar", "registered_at")}),
        (
            "Payment Info",
            {
                "fields": (
                    "payment_status",
                    "razorpay_order_id",
                    "razorpay_payment_id",
                    "razorpay_signature",
                )
            },
        ),
    )
