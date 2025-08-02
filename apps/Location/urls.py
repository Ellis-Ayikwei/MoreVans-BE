from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"locations", views.LocationViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "locations/validate-postcode/<str:postcode>/",
        views.validate_postcode,
        name="validate_postcode",
    ),
    path(
        "locations/postcode-suggestions/<str:postcode>/",
        views.validate_postcode,
        name="validate_postcode",
    ),
    # Google Maps API proxy endpoints - using simple Django views
    path(
        "locations/google-autocomplete/",
        views.google_address_autocomplete_simple,
        name="google_address_autocomplete",
    ),
    path(
        "locations/google-place-details/",
        views.google_place_details,
        name="google_place_details",
    ),
    path(
        "locations/geocode/",
        views.geocode_address,
        name="geocode_address",
    ),
    # Postcode suggestions - using simple Django view
    path(
        "locations/postcode-suggestions/",
        views.postcode_suggestions_simple,
        name="postcode_suggestions",
    ),
    # Enhanced postcode address lookup - gets all addresses for a postcode
    path(
        "locations/postcode-addresses/",
        views.postcode_address_lookup,
        name="postcode_address_lookup",
    ),
    path(
        "locations/postcode-addresses-enhanced/",
        views.postcode_address_lookup_enhanced,
        name="postcode_address_lookup_enhanced",
    ),
    # Comprehensive postcode validation endpoints
    path(
        "locations/validate-postcode-comprehensive/<str:postcode>/",
        views.validate_postcode_comprehensive,
        name="validate_postcode_comprehensive",
    ),
    path(
        "locations/postcode-addresses-comprehensive/<str:postcode>/",
        views.get_postcode_addresses_comprehensive,
        name="get_postcode_addresses_comprehensive",
    ),
]
