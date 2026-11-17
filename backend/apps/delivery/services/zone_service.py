from ..models import DeliveryZone
from common.exceptions import ZoneNotServiceableError


def get_serviceable_zone(address):
    # Maps customer postal code or coordinates to an active delivery zone
    postal_code = None
    lat = None
    lng = None

    if hasattr(address, 'postal_code'):
        postal_code = getattr(address, 'postal_code', None)
        lat = getattr(address, 'latitude', None)
        lng = getattr(address, 'longitude', None)
    elif isinstance(address, dict):
        postal_code = address.get('postal_code')
        lat = address.get('latitude') or address.get('lat')
        lng = address.get('longitude') or address.get('lng')
    elif isinstance(address, str):
        postal_code = address.strip()

    active_zones = DeliveryZone.objects.filter(is_active=True)

    # Check postal code match first
    if postal_code:
        clean_code = str(postal_code).strip()
        for zone in active_zones:
            if zone.is_postal_code_serviced(clean_code):
                return zone

    # Check coordinate radius match
    if lat is not None and lng is not None:
        try:
            f_lat = float(lat)
            f_lng = float(lng)
            for zone in active_zones:
                if zone.center_lat is not None and zone.center_lng is not None:
                    if zone.is_within_radius(f_lat, f_lng):
                        return zone
        except (ValueError, TypeError):
            pass

    identifier = postal_code or f"Coordinates ({lat}, {lng})"
    raise ZoneNotServiceableError(
        f"Delivery address '{identifier}' is not serviceable. We currently service configured Pune dark store zones."
    )
