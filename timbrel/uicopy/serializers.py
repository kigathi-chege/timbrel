from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from timbrel.base import BaseSerializer
from timbrel.utils import get_serializer_dict

from .models import Page, Section, Text, Button, Image, Data


class TextSerializer(BaseSerializer):
    class Meta:
        model = Text
        fields = "__all__"


class ButtonSerializer(BaseSerializer):
    button_text = TextSerializer(
        many=False, read_only=True, source="text", allow_null=True
    )

    class Meta:
        model = Button
        fields = "__all__"


class ImageSerializer(BaseSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = "__all__"

    def get_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class DataSerializer(BaseSerializer):
    class Meta:
        model = Data
        fields = "__all__"

    def to_representation(self, instance):
        try:
            content_type = ContentType.objects.get(id=instance.content_type_id)
            model_class = content_type.model_class()

            if model_class is None:
                raise ValueError("No model found for this content type.")

            # get all the filters from instance.filters
            # check if there is a page_size filter

            if "page_size" in instance.filters:
                print("PAGE SIZE IN FILTERS", content_type.model)
                page_size = int(instance.filters["page_size"])
                queryset = model_class.objects.all()[:page_size]
            else:
                print("PAGE SIZE NOT FOUND IN FILTERS", content_type.model)
                queryset = model_class.objects.all()

            serializer_dict = get_serializer_dict()
            serializer_class = serializer_dict.get(content_type.model)
            serialized_data = serializer_class(queryset, many=True).data

            return serialized_data

        except ObjectDoesNotExist:
            print("ContentType with this ID does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return super().to_representation(instance)


class SectionSerializer(BaseSerializer):
    section_texts = serializers.SerializerMethodField()
    section_buttons = serializers.SerializerMethodField()
    section_images = serializers.SerializerMethodField()
    child_sections = serializers.SerializerMethodField()
    section_data = serializers.SerializerMethodField()

    def get_section_texts(self, obj):
        return TextSerializer(obj.texts.order_by("sectiontext__order"), many=True).data

    def get_section_buttons(self, obj):
        return ButtonSerializer(
            obj.buttons.order_by("sectionbutton__order"), many=True
        ).data

    def get_section_images(self, obj):
        return ImageSerializer(
            obj.images.order_by("sectionimage__order"), many=True
        ).data

    def get_child_sections(self, obj):
        serializer = SectionSerializer(
            obj.children.order_by("child_sections__order"), many=True
        )
        return serializer.data

    def get_section_data(self, obj):
        return DataSerializer(obj.data, many=True).data

    class Meta:
        model = Section
        fields = "__all__"


class PageSerializer(BaseSerializer):
    page_sections = serializers.SerializerMethodField()
    # page_images = serializers.SerializerMethodField()

    def get_page_sections(self, obj):
        return SectionSerializer(
            obj.sections.order_by("pagesection__order"), many=True
        ).data

    class Meta:
        model = Page
        fields = "__all__"
