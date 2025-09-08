from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from .models import Booking, Payment
from .serializers import BookingSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from .payment_utils import chapa
from django.http import Http404
from .tasks import send_booking_confirmation

chapa_client = chapa()


# Create your views here.
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "property", "user", "start_date", "end_date"]

    def get_queryset(self):
        queryset = super().get_queryset()
        property_id = self.kwargs.get("property_pk")
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        return queryset

    def perform_create(self, serializer):
        booking = serializer.save()

        # Trigger async email task if user has email
        if booking.user and booking.user.email:
            send_booking_confirmation.delay(booking.id)  # type: ignore


class PaymentViewSet(viewsets.ViewSet):
    """
    Handles initiating and verifying payments for bookings.
    """

    @action(detail=True, methods=["post"], url_path="initiate")
    def initiate_payment(self, request, pk=None):
        try:
            booking = Booking.objects.get(id=pk, user=request.user)

            # Check if payment already exists
            if hasattr(booking, "payment"):
                return Response(
                    {"error": "Payment already initiated for this booking"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Call Chapa
            payment_response = chapa_client.initiate_payment(booking=booking)

            if (
                not payment_response
                or "status" not in payment_response
                or payment_response["status"] != "success"
            ):
                return Response(
                    {"error": "Failed to initiate payment"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            # Save payment record
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                transaction_id=payment_response["data"]["tx_ref"],
                chapa_response=payment_response,
            )

            return Response(
                {
                    "status": "success",
                    "checkout_url": payment_response["data"]["checkout_url"],
                    "transaction_id": payment.transaction_id,
                }
            )

        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"], url_path="verify")
    def verify_payment(self, request):
        transaction_id = request.query_params.get("tx_ref")

        if not transaction_id:
            return Response(
                {"error": "Transaction reference required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
        except Payment.DoesNotExist:
            raise Http404("Payment not found")

        data = chapa_client.verify_payment(transaction_id)

        if not data or data.get("status") != "success":
            payment.status = "failed"
            payment.save(update_fields=["status"])
            return Response({"status": "failed"}, status=status.HTTP_200_OK)

        payment.status = "completed"
        payment.chapa_response = data
        payment.save(update_fields=["status", "chapa_response"])

        # Trigger async confirmation email
        send_booking_confirmation.delay(payment.booking.id)  # type: ignore

        return Response({"status": "completed"}, status=status.HTTP_200_OK)


# class InitiatePaymentView(APIView):
#     def post(self, request, booking_id):
#         try:
#             booking = Booking.objects.get(id=booking_id, user=request.user)

#             # Check if payment already exists
#             if hasattr(booking, "payment"):
#                 return Response(
#                     {"error": "Payment already initiated for this booking"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Initiate payment with Chapa
#             payment_response = chapa.initiate_payment(booking=booking)

#             if (
#                 not payment_response
#                 or "status" not in payment_response
#                 or payment_response["status"] != "success"
#             ):
#                 return Response(
#                     {"error": "Failed to initiate payment"},
#                     status=status.HTTP_502_BAD_GATEWAY,
#                 )

#             # Create payment record
#             payment = Payment.objects.create(
#                 booking=booking,
#                 amount=booking.total_price,
#                 transaction_id=payment_response["data"]["tx_ref"],
#                 chapa_response=payment_response,
#             )

#             return Response(
#                 {
#                     "status": "success",
#                     "checkout_url": payment_response["data"]["checkout_url"],
#                     "transaction_id": payment.transaction_id,
#                 }
#             )

#         except Booking.DoesNotExist:
#             return Response(
#                 {"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND
#             )


# class VerifyPaymentView(APIView):
#     def get(self, request):
#         transaction_id = request.query_params.get("tx_ref")

#         if not transaction_id:
#             return Response(
#                 {"error": "Transaction reference required"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         try:
#             payment = Payment.objects.get(transaction_id=transaction_id)
#         except Payment.DoesNotExist:
#             raise Http404("Payment not found")

#         data = chapa.verify_payment(transaction_id)

#         if not data or data.get("status") != "success":
#             payment.status = "failed"
#             payment.save(update_fields=["status"])
#             return Response({"status": "failed"}, status=status.HTTP_200_OK)

#         payment.status = "completed"
#         payment.chapa_response = data
#         payment.save(update_fields=["status", "chapa_response"])

#         send_booking_confirmation.delay(payment.booking.id)

#         return Response({"status": "completed"}, status=status.HTTP_200_OK)
