from django.urls import path, include

from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r"payments", PaymentViewSet, basename="payment")


# # Nested router
# properties_router = NestedDefaultRouter(router, r"properties", lookup="property")
# properties_router.register(r"bookings", BookingViewSet, basename="property-bookings")
# router = DefaultRouter()
# router.register(r'listings', ListingViewSet)
# router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
