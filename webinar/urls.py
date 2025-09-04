from django.urls import path
from .views import (
    WebinarListCreateView,
    WebinarDetailView,
    RegisterWebinarView,
    VerifyPaymentView,
    DashboardView,
    MyRegistrationsView,
    WebinarAttendeesView,
    cancel_registration,
)

urlpatterns = [
    # Webinars
    path("webinars/", WebinarListCreateView.as_view(), name="webinar-list-create"),
    path("webinars/<int:pk>/", WebinarDetailView.as_view(), name="webinar-detail"),
    # Registration
    path("webinars/register/", RegisterWebinarView.as_view(), name="register-webinar"),
    path("registrations/", MyRegistrationsView.as_view(), name="my-registrations"),
    path(
        "registrations/<int:registration_id>/cancel/",
        cancel_registration,
        name="cancel-registration",
    ),
    # Attendees (host/admin only)
    path(
        "webinars/<int:webinar_id>/attendees/",
        WebinarAttendeesView.as_view(),
        name="webinar-attendees",
    ),
    # Payments
    path("payments/verify/", VerifyPaymentView.as_view(), name="verify-payment"),
    # Dashboard
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
