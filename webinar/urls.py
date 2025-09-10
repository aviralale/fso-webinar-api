# urls.py for webinar app
from django.urls import path
from . import views

urlpatterns = [
    # Webinar management
    path(
        "webinars/", views.WebinarListCreateView.as_view(), name="webinar-list-create"
    ),
    path(
        "webinars/<int:pk>/", views.WebinarDetailView.as_view(), name="webinar-detail"
    ),
    # Registration (now supports anonymous users)
    path(
        "webinars/register/",
        views.RegisterWebinarView.as_view(),
        name="register-webinar",
    ),
    path("verify-payment/", views.VerifyPaymentView.as_view(), name="verify-payment"),
    # Registration status check (for anonymous users)
    path(
        "registration-status/<int:registration_id>/",
        views.check_registration_status,
        name="check-registration-status",
    ),
    # User dashboard (requires authentication)
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path(
        "my-registrations/",
        views.MyRegistrationsView.as_view(),
        name="my-registrations",
    ),
    # Webinar management (requires authentication)
    path(
        "webinars/<int:webinar_id>/attendees/",
        views.WebinarAttendeesView.as_view(),
        name="webinar-attendees",
    ),
    path(
        "registrations/<int:registration_id>/cancel/",
        views.cancel_registration,
        name="cancel-registration",
    ),
]
