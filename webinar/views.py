import razorpay
from datetime import timedelta
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Webinar, Registration
from .serializers import (
    WebinarSerializer,
    WebinarListSerializer,
    RegistrationSerializer,
    PaymentVerificationSerializer,
    AnonymousRegistrationSerializer,
)
from .permissions import IsAdminUser, IsAdminOrHostOwner
from accounts.models import User
from .email_service import WebinarEmailService


# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


class WebinarListCreateView(generics.ListCreateAPIView):
    queryset = Webinar.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return WebinarListSerializer
        return WebinarSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [permissions.IsAuthenticatedOrAllowAny()]

    def get_queryset(self):
        queryset = Webinar.objects.all()

        # For authenticated users, apply role-based filtering
        if self.request.user.is_authenticated:
            # Filter future webinars for attendees
            if self.request.user.role == "attendee":
                queryset = queryset.filter(start_time__gt=timezone.now())

            # Filter host's webinars
            elif self.request.user.role == "host":
                queryset = queryset.filter(host=self.request.user)
        else:
            # For anonymous users, show all future webinars
            queryset = queryset.filter(start_time__gt=timezone.now())

        return queryset


class WebinarDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Webinar.objects.all()
    serializer_class = WebinarSerializer
    permission_classes = [
        permissions.AllowAny
    ]  # Allow anonymous access to view details

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminOrHostOwner()]
        return [permissions.AllowAny()]


class RegisterWebinarView(APIView):
    permission_classes = [permissions.AllowAny]  # Allow anonymous registration

    def post(self, request):
        try:
            webinar_id = request.data.get("webinar_id")
            webinar = Webinar.objects.get(id=webinar_id)

            # For anonymous users, collect registration details
            if not request.user.is_authenticated:
                # Use anonymous registration serializer to validate guest details
                guest_serializer = AnonymousRegistrationSerializer(data=request.data)
                if not guest_serializer.is_valid():
                    return Response(
                        guest_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

                guest_data = guest_serializer.validated_data
                guest_email = guest_data["email"]
                guest_name = guest_data["name"]
                guest_phone = guest_data.get("phone", "")

                # Check if someone with this email is already registered
                existing_registration = Registration.objects.filter(
                    webinar=webinar, guest_email=guest_email
                ).first()

                if existing_registration:
                    return Response(
                        {
                            "error": "Someone with this email is already registered for this webinar."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user = None
            else:
                # Authenticated user registration
                if Registration.objects.filter(
                    user=request.user, webinar=webinar
                ).exists():
                    return Response(
                        {"error": "You are already registered for this webinar."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user = request.user
                guest_email = None
                guest_name = None
                guest_phone = None

            # Check capacity
            if webinar.is_full:
                return Response(
                    {"error": "Webinar is full."}, status=status.HTTP_400_BAD_REQUEST
                )

            # Check if webinar has already started
            if webinar.start_time <= timezone.now():
                return Response(
                    {"error": "Cannot register for past webinars."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create registration
            registration = Registration.objects.create(
                user=user,
                webinar=webinar,
                guest_email=guest_email,
                guest_name=guest_name,
                guest_phone=guest_phone,
            )

            # Handle payment
            if webinar.price > 0:
                # Create Razorpay order
                order_data = {
                    "amount": int(webinar.price * 100),  # Amount in paise
                    "currency": "INR",
                    "receipt": f"webinar_{webinar.id}_reg_{registration.id}",
                    "notes": {
                        "webinar_id": webinar.id,
                        "registration_id": registration.id,
                        "user_id": user.id if user else None,
                        "guest_email": guest_email if guest_email else None,
                    },
                }

                try:
                    razorpay_order = razorpay_client.order.create(order_data)
                    registration.razorpay_order_id = razorpay_order["id"]
                    registration.save()

                    return Response(
                        {
                            "success": True,
                            "registration_id": registration.id,
                            "razorpay_order_id": razorpay_order["id"],
                            "amount": webinar.price,
                            "currency": "INR",
                            "key": settings.RAZORPAY_KEY_ID,
                        }
                    )
                except Exception as e:
                    registration.delete()
                    return Response(
                        {"error": f"Payment order creation failed: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                # Free webinar - mark as successful and send confirmation email
                registration.payment_status = "success"
                registration.save()

                # Send registration confirmation email
                WebinarEmailService.send_registration_confirmation(registration)

                return Response(
                    {
                        "success": True,
                        "message": "Successfully registered for free webinar.",
                        "registration_id": registration.id,
                    }
                )

        except Webinar.DoesNotExist:
            return Response(
                {"error": "Webinar not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPaymentView(APIView):
    permission_classes = [permissions.AllowAny]  # Allow anonymous payment verification

    def post(self, request):
        serializer = PaymentVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            registration = Registration.objects.get(
                id=serializer.validated_data["registration_id"]
            )

            # For authenticated users, verify ownership
            if request.user.is_authenticated and registration.user != request.user:
                return Response(
                    {"error": "Registration not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Verify Razorpay signature
            params_dict = {
                "razorpay_order_id": serializer.validated_data["razorpay_order_id"],
                "razorpay_payment_id": serializer.validated_data["razorpay_payment_id"],
                "razorpay_signature": serializer.validated_data["razorpay_signature"],
            }

            try:
                razorpay_client.utility.verify_payment_signature(params_dict)

                # Update registration
                registration.payment_status = "success"
                registration.razorpay_payment_id = serializer.validated_data[
                    "razorpay_payment_id"
                ]
                registration.razorpay_signature = serializer.validated_data[
                    "razorpay_signature"
                ]
                registration.save()

                # Send registration confirmation email
                WebinarEmailService.send_registration_confirmation(registration)

                return Response(
                    {
                        "success": True,
                        "message": "Payment verified successfully.",
                        "registration": RegistrationSerializer(registration).data,
                    }
                )

            except razorpay.errors.SignatureVerificationError:
                registration.payment_status = "failed"
                registration.save()

                return Response(
                    {"error": "Invalid payment signature."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Registration.DoesNotExist:
            return Response(
                {"error": "Registration not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == "attendee":
            # Return attendee's registered webinars
            registrations = Registration.objects.filter(
                user=user, payment_status="success"
            ).select_related("webinar")

            upcoming_webinars = []
            past_webinars = []

            for reg in registrations:
                webinar_data = {
                    "id": reg.webinar.id,
                    "title": reg.webinar.title,
                    "start_time": reg.webinar.start_time,
                    "duration_minutes": reg.webinar.duration_minutes,
                    "host_name": reg.webinar.host.get_full_name(),
                    "registered_at": reg.registered_at,
                    "price": reg.webinar.price,
                }

                if reg.webinar.start_time > timezone.now():
                    upcoming_webinars.append(webinar_data)
                else:
                    past_webinars.append(webinar_data)

            return Response(
                {
                    "role": "attendee",
                    "upcoming_webinars": upcoming_webinars,
                    "past_webinars": past_webinars,
                    "total_registrations": len(registrations),
                }
            )

        elif user.role == "host":
            # Return host's webinars and their attendees
            webinars = Webinar.objects.filter(host=user).prefetch_related(
                "registrations__user"
            )

            webinar_data = []
            total_attendees = 0
            total_revenue = 0

            for webinar in webinars:
                successful_registrations = webinar.registrations.filter(
                    payment_status="success"
                )
                attendees = []

                for reg in successful_registrations:
                    # Handle both authenticated users and anonymous registrations
                    if reg.user:
                        attendee_name = reg.user.get_full_name()
                        attendee_email = reg.user.email
                    else:
                        attendee_name = reg.guest_name
                        attendee_email = reg.guest_email

                    attendees.append(
                        {
                            "id": reg.user.id if reg.user else None,
                            "name": attendee_name,
                            "email": attendee_email,
                            "phone": reg.guest_phone if not reg.user else None,
                            "registered_at": reg.registered_at,
                        }
                    )

                revenue = len(successful_registrations) * webinar.price
                total_revenue += revenue
                total_attendees += len(successful_registrations)

                webinar_data.append(
                    {
                        "id": webinar.id,
                        "title": webinar.title,
                        "start_time": webinar.start_time,
                        "capacity": webinar.capacity,
                        "registered_count": len(successful_registrations),
                        "price": webinar.price,
                        "revenue": revenue,
                        "attendees": attendees,
                    }
                )

            return Response(
                {
                    "role": "host",
                    "webinars": webinar_data,
                    "total_webinars": len(webinars),
                    "total_attendees": total_attendees,
                    "total_revenue": float(total_revenue),
                }
            )

        elif user.role == "admin":
            # Return global statistics
            total_webinars = Webinar.objects.count()
            total_users = User.objects.count()
            total_registrations = Registration.objects.filter(
                payment_status="success"
            ).count()
            total_revenue = (
                Registration.objects.filter(payment_status="success").aggregate(
                    revenue=Sum("webinar__price")
                )["revenue"]
                or 0
            )

            # Recent activity
            recent_registrations = Registration.objects.filter(
                payment_status="success",
                registered_at__gte=timezone.now() - timezone.timedelta(days=7),
            ).select_related("user", "webinar")[:10]

            recent_activity = []
            for reg in recent_registrations:
                # Handle both authenticated users and anonymous registrations
                if reg.user:
                    user_name = reg.user.get_full_name()
                else:
                    user_name = f"{reg.guest_name} (Guest)"

                recent_activity.append(
                    {
                        "user": user_name,
                        "webinar": reg.webinar.title,
                        "registered_at": reg.registered_at,
                        "amount": reg.webinar.price,
                    }
                )

            # Upcoming webinars
            upcoming_webinars = Webinar.objects.filter(
                start_time__gt=timezone.now()
            ).order_by("start_time")[:5]

            upcoming_data = []
            for webinar in upcoming_webinars:
                upcoming_data.append(
                    {
                        "id": webinar.id,
                        "title": webinar.title,
                        "start_time": webinar.start_time,
                        "registered_count": webinar.registered_count,
                        "capacity": webinar.capacity,
                        "host_name": webinar.host.get_full_name(),
                    }
                )

            return Response(
                {
                    "role": "admin",
                    "total_webinars": total_webinars,
                    "total_users": total_users,
                    "total_registrations": total_registrations,
                    "total_revenue": float(total_revenue),
                    "recent_activity": recent_activity,
                    "upcoming_webinars": upcoming_data,
                }
            )


class MyRegistrationsView(generics.ListAPIView):
    """
    List current user's registrations
    """

    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user)


class WebinarAttendeesView(generics.ListAPIView):
    """
    List attendees for a specific webinar (host/admin only)
    """

    serializer_class = RegistrationSerializer
    permission_classes = [IsAdminOrHostOwner]

    def get_queryset(self):
        webinar_id = self.kwargs["webinar_id"]
        return Registration.objects.filter(
            webinar_id=webinar_id, payment_status="success"
        ).select_related("user", "webinar")

    def get_object(self):
        """Get the webinar for permission checking"""
        return Webinar.objects.get(id=self.kwargs["webinar_id"])


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def cancel_registration(request, registration_id):
    """
    Cancel a registration (only if webinar hasn't started and payment can be refunded)
    """
    try:
        registration = Registration.objects.get(id=registration_id, user=request.user)

        # Check if webinar has started
        if registration.webinar.start_time <= timezone.now():
            return Response(
                {"error": "Cannot cancel registration for started webinars."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if cancellation is allowed (e.g., at least 24 hours before start)
        cancellation_deadline = registration.webinar.start_time - timedelta(hours=24)
        if timezone.now() > cancellation_deadline:
            return Response(
                {"error": "Cancellation deadline has passed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # For paid webinars, implement refund logic
        if registration.webinar.price > 0 and registration.payment_status == "success":
            try:
                refund = razorpay_client.payment.refund(
                    registration.razorpay_payment_id,
                    {
                        "amount": int(registration.webinar.price * 100),
                        "notes": {
                            "reason": "User cancellation",
                            "registration_id": registration.id,
                        },
                    },
                )
                registration.payment_status = "failed"  # Mark as cancelled
                registration.save()

                return Response(
                    {
                        "success": True,
                        "message": "Registration cancelled and refund initiated.",
                        "refund_id": refund["id"],
                    }
                )
            except Exception as e:
                return Response(
                    {"error": f"Refund failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            # Free webinar - just delete registration
            registration.delete()
            return Response(
                {"success": True, "message": "Registration cancelled successfully."}
            )

    except Registration.DoesNotExist:
        return Response(
            {"error": "Registration not found."}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def check_registration_status(request, registration_id):
    """
    Check registration status for anonymous users
    """
    try:
        registration = Registration.objects.get(id=registration_id)

        return Response(
            {
                "registration_id": registration.id,
                "webinar_title": registration.webinar.title,
                "payment_status": registration.payment_status,
                "webinar_start_time": registration.webinar.start_time,
                "webinar_link": (
                    registration.webinar.link
                    if registration.payment_status == "success"
                    else None
                ),
            }
        )

    except Registration.DoesNotExist:
        return Response(
            {"error": "Registration not found."}, status=status.HTTP_404_NOT_FOUND
        )
