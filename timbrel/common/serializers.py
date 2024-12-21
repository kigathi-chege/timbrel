import os
import mimetypes
import hashlib
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import serializers
from rest_framework.reverse import reverse


from timbrel.base import BaseSerializer
from .models import (
    Tag,
    File,
    Advertisement,
    Article,
    Facet,
    FacetValue,
)


class TagSerializer(BaseSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "url",
            "description",
            "tags",
            "absolute_url",
        ]


class FileSerializer(BaseSerializer):
    file = serializers.FileField(write_only=True)
    name = serializers.CharField(required=False)
    folder = serializers.CharField(write_only=True, max_length=100, required=False)

    def create(self, validated_data):
        file = validated_data["file"]
        upload_folder = (
            validated_data["folder"] if "folder" in validated_data else "general"
        )

        file_extension = os.path.splitext(file.name)[1]
        file_mime_type, _ = mimetypes.guess_type(file.name)

        hash_obj = hashlib.new("md5")
        file_content = file.read()
        hash_obj.update(file_content)
        checksum = hash_obj.hexdigest()

        """ 
        Check if there is an existing file with the same checksum
        If exists update usage_count by one and return
        """
        if existing_file := File.objects.filter(checksum=checksum).first():
            existing_file.usagecount += 1
            existing_file.save()
            return existing_file

        upload_file_path = f"{upload_folder}/{uuid.uuid4()}{file_extension}"
        file_path = default_storage.save(upload_file_path, file)

        file_data = {
            "name": validated_data["name"] if "name" in validated_data else file.name,
            "description": (
                validated_data["description"]
                if "description" in validated_data
                else None
            ),
            "path": file_path,
            "size": file.size,
            "extension": file_extension,
            "mimetype": file_mime_type,
            "checksum": checksum,
        }

        file = File.objects.create(**file_data)
        file.url = settings.APP_URL + reverse("timbrel-file-view", args=[file.id])
        file.save()
        return file

    class Meta:
        model = File
        fields = "__all__"


class AdvertisementSerializer(BaseSerializer):
    class Meta:
        model = Advertisement
        fields = "__all__"


class ArticleSerializer(BaseSerializer):
    class Meta:
        model = Article
        fields = "__all__"


class FacetSerializer(BaseSerializer):
    class Meta:
        model = Facet
        fields = "__all__"


class FacetValueSerializer(BaseSerializer):
    class Meta:
        model = FacetValue
        fields = "__all__"
