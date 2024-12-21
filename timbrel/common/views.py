from django.utils import timezone
from django.http import StreamingHttpResponse
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from timbrel.base import BaseViewSet
from .serializers import (
    TagSerializer,
    FileSerializer,
    AdvertisementSerializer,
    ArticleSerializer,
    FacetSerializer,
    FacetValueSerializer,
)
from .models import (
    Tag,
    File,
    Advertisement,
    Article,
    Facet,
    FacetValue,
)
from .filters import AdvertisementFilter


class TagViewSet(BaseViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["name", "url", "description"]
    filterset_fields = ["name", "url", "description"]


class FacetViewSet(BaseViewSet):
    queryset = Facet.objects.all()
    serializer_class = FacetSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["name", "url", "description"]
    filterset_fields = ["name", "url", "description"]


class FacetValueViewSet(BaseViewSet):
    queryset = FacetValue.objects.all()
    serializer_class = FacetValueSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["name", "url", "description"]
    filterset_fields = ["name", "url", "description", "facet"]


class FileViewSet(BaseViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["name", "url", "description"]
    filterset_fields = [
        "name",
        "url",
        "description",
        "size",
        "extension",
        "mimetype",
        "usagecount",
        "viewed_at",
    ]

    @action(detail=True, methods=["get"], url_name="view")
    def view(self, request, pk=None):
        file = self.get_object()
        file.viewed_at = timezone.now()
        file.save()
        if not default_storage.exists(file.path):
            return Response(
                {"error": "File not found"}, status=status.HTTP_404_NOT_FOUND
            )

        file_stream = default_storage.open(file.path, "rb")

        response = StreamingHttpResponse(
            file_stream, content_type=file.mimetype or "application/octet-stream"
        )
        response["Content-Disposition"] = f'inline; filename="{file.name}"'
        return response


class AdvertisementViewSet(BaseViewSet):
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["ad_type", "title", "description", "url"]
    filterset_class = AdvertisementFilter


class ArticleViewSet(BaseViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["title", "content", "description", "url"]
