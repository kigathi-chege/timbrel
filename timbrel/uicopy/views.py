from rest_framework import permissions

from timbrel.base import BaseViewSet

from .serializers import (
    TextSerializer,
    DataSerializer,
    SectionSerializer,
    PageSerializer,
)
from .models import Text, Data, Section, Page


class TextViewSet(BaseViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["title", "content", "slug"]


class DataViewSet(BaseViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]


class SectionViewSet(BaseViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["title", "description", "slug"]


class PageViewSet(BaseViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["email", "phone", "username", "slug"]
