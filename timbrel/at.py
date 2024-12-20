import africastalking
from django.conf import settings


username = settings.AFRICASTALKING_USERNAME
api_key = settings.AFRICASTALKING_API_KEY
africastalking.initialize(username, api_key)

sms = africastalking.SMS


def on_finish(error, response):
    if error is not None:
        raise error
    print(response)
