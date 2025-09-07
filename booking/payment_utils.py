import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework import viewsets, filters, status

CHAPA_API_URL = "https://api.chapa.co/v1/transaction/"
CHAPA_INIT_URL = f"{CHAPA_API_URL}initialize"
CHAPA_VERIFY_URL = f"{CHAPA_API_URL}verify"
CHAPA_SECRET = settings.CHAPA_SECRET_KEY


class chapa:
    def __init__(self):
        self.__headers = {
            "Authorization": f"Bearer {CHAPA_SECRET}",
            "Content-Type": "application/json",
        }

    def initiate_payment(self, booking, curr="USD"):
        payload = {
            "amount": str(booking.total_price),
            "currency": curr,
            "email": booking.user.email,
            "first_name": booking.user.first_name,
            "last_name": booking.user.last_name,
            "tx_ref": f"booking-{booking.id}-{booking.created_at.timestamp()}",
            "callback_url": f"{settings.BASE_URL}/api/payments/verify/",
            "return_url": f"{settings.FRONTEND_URL}/bookings/{booking.id}/status",
            "customization": {
                "title": "ALX Travel Booking",
                "description": f"Payment for booking #{booking.id}",
            },
        }

        try:
            response = requests.post(
                CHAPA_INIT_URL, json=payload, headers=self.__headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Chapa API Error: {e}")
            return None

    def verify_payment(self, tid: str):
        try:
            response = requests.get(
                f"{CHAPA_VERIFY_URL}{tid}",
                headers=self.__headers,
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass  # log error if needed

        return None
