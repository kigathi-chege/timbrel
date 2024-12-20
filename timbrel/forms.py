import os
import mimetypes
import hashlib
import uuid

from django import forms
from django.db import models
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework.reverse import reverse
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldAdminTextInputWidget

from .models import File


class BaseForm(forms.ModelForm):
    formfield_overrides = {
        models.TextField: {
            "description": WysiwygWidget,
        }
    }
    pass


class EditFileAdminForm(BaseForm):
    name = forms.CharField(label="Name", widget=UnfoldAdminTextInputWidget)
    description = forms.CharField(
        label="Description", widget=WysiwygWidget, required=False
    )

    class Meta:
        model = File
        fields = ["name", "description"]


class FileAdminForm(BaseForm):
    file = forms.FileField(label="File", widget=UnfoldAdminFileFieldWidget)
    name = forms.CharField(label="Name", widget=UnfoldAdminTextInputWidget)
    description = forms.CharField(
        label="Description", widget=WysiwygWidget, required=False
    )

    class Meta:
        model = File
        fields = ["file", "name", "description"]

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")

        if not file:
            self.add_error(
                "file",
                "FIle not found. Please select a file to upload.",
            )
            return cleaned_data

        hash_obj = hashlib.new("md5")
        file_content = file.read()
        hash_obj.update(file_content)
        checksum = hash_obj.hexdigest()

        if existing_file := File.objects.filter(checksum=checksum).first():
            self.add_error(
                "file",
                f"File already exists under name: {existing_file.name}. Please use this file instead of uploading a new one.",
            )

        return cleaned_data

    def save(self, commit=True):
        file = self.cleaned_data["file"]
        upload_folder = "general"

        # Extract file size, extension, and MIME type
        file_extension = os.path.splitext(file.name)[1]
        file_mime_type, _ = mimetypes.guess_type(file.name)

        hash_obj = hashlib.new("md5")
        file_content = file.read()
        hash_obj.update(file_content)
        checksum = hash_obj.hexdigest()

        # generate a unique name with original extension
        upload_file_path = f"{upload_folder}/{uuid.uuid4()}.{file_extension}"
        file_path = default_storage.save(upload_file_path, file)

        self.instance.name = (
            self.cleaned_data["name"] if "name" in self.cleaned_data else file.name
        )
        self.instance.description = (
            self.cleaned_data["description"]
            if "description" in self.cleaned_data
            else None
        )

        reverse_url = reverse("timbrel-file-view", args=[self.instance.id])
        file_url = settings.APP_URL + reverse_url

        self.instance.path = file_path
        self.instance.size = file.size
        self.instance.url = file_url
        self.instance.extension = file_extension
        self.instance.mimetype = file_mime_type
        self.instance.checksum = checksum

        return super().save(commit)
