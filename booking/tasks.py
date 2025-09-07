from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking


@shared_task
def send_booking_confirmation(booking_id):
    booking = Booking.objects.get(id=booking_id)
    subject = f"Booking Confirmation #{booking.id}"
    message = f"Your booking for {booking.property.name} has been confirmed!\n\nTotal: {booking.total_price}"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [booking.user.email]

    send_mail(
        subject,
        message,
        from_email,
        to_email,
        fail_silently=False,
    )
