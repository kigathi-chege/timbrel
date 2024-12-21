import googlemaps

from django.conf import settings
from rest_framework.validators import ValidationError

gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)


def get_distance(origin, destination):
    return gmaps.distance_matrix(origin, destination)["rows"][0]["elements"][0]


def get_directions(origin, destination):
    return gmaps.directions(origin, destination)


def get_elevation(locations):
    return gmaps.elevation(locations)


def get_geocode(address):
    return gmaps.geocode(address)


def get_reverse_geocode(lat, lng):
    return gmaps.reverse_geocode((lat, lng))


def get_place(place_id):
    return gmaps.place(place_id)


def retrieve(string):
    geocode = get_geocode(string)

    if not geocode:
        try:
            geoplace = get_place(string)
            delivery_address = geoplace["result"]["formatted_address"]
            latitude = geoplace["result"]["geometry"]["location"]["lat"]
            longitude = geoplace["result"]["geometry"]["location"]["lng"]
        except:
            raise ValidationError(
                "Invalid delivery address. Please enter a valid address."
            )
    else:
        delivery_address = geocode[0]["formatted_address"]
        latitude = geocode[0]["geometry"]["location"]["lat"]
        longitude = geocode[0]["geometry"]["location"]["lng"]

    return delivery_address, latitude, longitude
