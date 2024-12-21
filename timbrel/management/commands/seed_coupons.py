from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from timbrel.utils import command_log
from timbrel.payment.models import Coupon


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        self.create_holiday_coupons()

    def create_holiday_coupons(self):
        command_log(
            self,
            f"Creating holiday coupons",
        )
        holidays = {
            "New Year's Day": "01-01",  # January 1st
            "Good Friday": "04-07",  # This will change every year
            "Easter Sunday": "06-04",  # Example, this should be calculated per year
            "Labour Day": "05-01",  # May 1st
            "Madaraka Day": "06-01",  # June 1st
            "Independence Day": "12-12",  # December 12th
            "Christmas Day": "25-12",  # December 25th
        }

        holiday_coupons = [
            {
                "code": "NEWYEAR2024",
                "discount": 10,
                "is_percentage": True,
                "valid_from": timezone.datetime(2024, 1, 1),
                "valid_to": timezone.datetime(2024, 1, 31),
            },
            {
                "code": "LABOURDAY2024",
                "discount": 15,
                "is_percentage": True,
                "valid_from": timezone.datetime(2024, 5, 1),
                "valid_to": timezone.datetime(2024, 5, 31),
            },
            {
                "code": "MADARAKADAY2024",
                "discount": 20,
                "is_percentage": True,
                "valid_from": timezone.datetime(2024, 6, 1),
                "valid_to": timezone.datetime(2024, 6, 30),
            },
            {
                "code": "MASHUJAA2024",
                "discount": 25,
                "is_percentage": True,
                "valid_from": timezone.datetime(2024, 10, 20),
                "valid_to": timezone.datetime(2024, 10, 31),
            },
            {
                "code": "JAMHURI2024",
                "discount": 30,
                "is_percentage": True,
                "valid_from": timezone.datetime(2024, 12, 12),
                "valid_to": timezone.datetime(2024, 12, 31),
            },
            {
                "code": "CHRISTMAS2024",
                "discount": 40,
                "is_percentage": True,
                "valid_from": timezone.datetime(2024, 12, 25),
                "valid_to": timezone.datetime(2024, 12, 26),
            },
        ]

        for coupon_data in holiday_coupons:
            Coupon.objects.get_or_create(
                code=coupon_data["code"],
                defaults={
                    "discount": coupon_data["discount"],
                    "is_percentage": coupon_data["is_percentage"],
                    "valid_from": coupon_data["valid_from"],
                    "valid_to": coupon_data["valid_to"],
                    # Optional: Set usage_limit and other fields as needed
                },
            )

        for holiday_name, holiday_date in holidays.items():
            # Create a new coupon
            coupon, created = Coupon.objects.get_or_create(
                code=f"{holiday_name.replace(' ', '').upper()}2024",  # Example code like MADARAKADAY2024
                defaults={
                    "discount": 10.00,  # 10% discount by default
                    "is_percentage": True,
                    "valid_from": timezone.make_aware(
                        timezone.datetime.strptime(f"2024-{holiday_date}", "%Y-%d-%m")
                    ),
                    "valid_to": timezone.make_aware(
                        timezone.datetime.strptime(f"2024-{holiday_date}", "%Y-%d-%m")
                        + timedelta(days=1)  # Valid for one day
                    ),
                    "usage_limit": 100,  # Limit usage to 100 times
                    "used_count": 0,
                    "active": True,
                },
            )
            if created:
                print(f"Coupon for {holiday_name} created.")
            else:
                print(f"Coupon for {holiday_name} already exists.")
