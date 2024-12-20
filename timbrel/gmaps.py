import googlemaps

from django.conf import settings

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
