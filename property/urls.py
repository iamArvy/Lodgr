from django.urls import path, include

from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, ReviewViewSet
from rest_framework_nested.routers import NestedDefaultRouter
from booking.views import BookingViewSet

router = DefaultRouter()
router.register(r"properties", PropertyViewSet)

# Nested router
properties_router = NestedDefaultRouter(router, r"properties", lookup="property")
properties_router.register(r"bookings", BookingViewSet, basename="property-bookings")
properties_router.register(r"reviews", ReviewViewSet, basename="property-reviews")

# router = DefaultRouter()
# router.register(r'listings', ListingViewSet)
# router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(properties_router.urls)),
]
