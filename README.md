============
timbrel
============

timbrel is a Django app to provide the basic framework for ecommerce.

Detailed documentation is in the "docs" directory.

## Quick start

1. Add "timbrel" to your INSTALLED_APPS setting like this::

   INSTALLED_APPS = [
   ...,
   "timbrel",
   ]

2. Include the timbrel URLconf in your project urls.py like this::

   path("timbrel/", include("timbrel.urls")),

3. Run `python manage.py migrate` to create the models.

<!-- 4. Start the development server and visit the admin to create a poll.

5. Visit the ``/timbrel/`` URL to participate in the poll. -->
