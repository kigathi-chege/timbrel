import json
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from timbrel.utils import command_log

from timbrel.models import (
    Page,
    Section,
    PageSection,
    Data,
    SectionData,
    Text,
    SectionText,
)


class Command(BaseCommand):
    help = "Imports page data from a JSON file into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file", type=str, help="The path to the JSON file to import"
        )

    def handle(self, *args, **kwargs):
        json_file = kwargs["json_file"]

        pages = json.load(open(json_file))

        for page in pages:
            ipage, created = Page.objects.get_or_create(title=page["name"])
            command_log(
                self, f"Page {page['name']} { 'created' if created else 'updated' }"
            )

            self.create_page_sections(ipage, page["sections"])

    def create_page_sections(self, page, sections):
        command_log(self, f"Creating page sections...")
        for index, section in enumerate(sections):
            isection, created = Section.objects.get_or_create(title=section["title"])
            command_log(
                self,
                f"Section {section['title']} { 'created' if created else 'updated' }",
            )
            page_section, pg_created = PageSection.objects.get_or_create(
                page=page, section=isection, order=index
            )
            command_log(
                self,
                f"Page section {index} for {section['title']} { 'created' if pg_created else 'updated' }",
            )

            self.create_section_data(section, isection)
            self.create_section_texts(section, isection)
            # self.create_section_buttons(section, page_section, index)
            # self.create_section_images(section, page_section, index)

    def create_section_data(self, section, isection):
        if "data" in section:
            command_log(self, f"Data found in section")
            for index, item in enumerate(section["data"]):
                content_type = ContentType.objects.get(model=item["model"].lower())
                filters = item.get("filters", {})

                data, d_created = Data.objects.get_or_create(
                    content_type=content_type, filters=filters
                )

                command_log(
                    self,
                    f"Data {index} for {section['title']} { 'created' if d_created else 'updated' }",
                )

                SectionData.objects.get_or_create(section=isection, data=data)

    def create_section_texts(self, section, isection):
        if "texts" in section:
            for index, text in enumerate(section["texts"]):
                itext, created = Text.objects.get_or_create(
                    content=text,
                )

                command_log(
                    self,
                    f"Section text {index} for {section['title']} { 'created' if created else 'updated' }",
                )

                SectionText.objects.get_or_create(
                    section=isection, text=itext, order=index
                )
