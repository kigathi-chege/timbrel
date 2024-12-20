import json
from django.core.management.base import BaseCommand
from timbrel.models import Tag


class Command(BaseCommand):
    help = "Imports data from a JSON file into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file", type=str, help="The path to the JSON file to import"
        )

    def handle(self, *args, **kwargs):
        json_file = kwargs["json_file"]

        try:
            with open(json_file, "r") as file:
                data = file.read()
                parsed_data = json.loads(data)

                for item in parsed_data:
                    print(f"Seeding {item['name']}")
                    self.create_tag(item)

            self.stdout.write(self.style.SUCCESS("Data imported successfully!"))

        except FileNotFoundError:
            self.stderr.write(f"Error: File {json_file} not found.")
        except json.JSONDecodeError as e:
            self.stderr.write(f"Error decoding JSON: {e}")

    def create_tag(self, item, parent=None):
        print(f"Creating tag {item['name']}")
        tag, _ = Tag.objects.get_or_create(name=item["name"])

        if parent:
            parent.tags.add(tag)

        if "tags" in item:
            print(f"Found children tags in {item['name']}")
            for tag_item in item["tags"]:
                print(f"Seeding child tag {tag_item['name']} for {item['name']}")
                self.create_tag(tag_item, tag)
