import hashlib
import hmac
from django.conf import settings


def verify_razorpay_signature(
    razorpay_order_id, razorpay_payment_id, razorpay_signature
):
    """
    Verify Razorpay payment signature
    """
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(generated_signature, razorpay_signature)
