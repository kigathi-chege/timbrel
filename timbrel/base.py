import uuid
import inflect

from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.db.models.fields.related import ManyToManyField
from django.db.models import (
    ForeignKey,
    ManyToManyField,
    OneToOneField,
    ManyToOneRel,
    OneToOneRel,
    ManyToManyRel,
)
from django.core.exceptions import FieldDoesNotExist
from django.conf import settings
from rest_framework import viewsets, serializers
from simple_history.models import HistoricalRecords

p = inflect.engine()


class CommonModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(
        max_length=200, default=uuid.uuid4, editable=False, unique=True
    )
    description = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def get_absolute_url(self):
        model_name = self.__class__.__name__.lower()
        try:
            return reverse(f"{model_name}-detail", args=[str(self.id)])
        except NoReverseMatch:
            return reverse(f"timbrel-{model_name}-detail", args=[str(self.id)])

    def get_relative_url(self):
        absolute_url = self.get_absolute_url()
        versionifier = f"/api/v{settings.APP_VERSION}"
        return absolute_url.replace(versionifier, "")

    def get_slug_source(self):
        """
        Returns the column from which the slug should be generated.
        This can be overridden by a child models as needed.
        """
        return "name"

    def get_slug_alt_source(self):
        """
        Returns an alternative column from which the slug should be generated.
        This can be overridden by a child models as needed.
        """
        return "title"

    def exclude_from_representation(self):
        """
        Returns a list of fields to exclude from the representation.
        This can be overridden by a child models as needed.
        """
        return ["slug", "created_at", "updated_at"]

    def include_in_representation(self):
        """
        Returns a list of fields to include in the representation.
        This can be overridden by a child models as needed.
        """
        return ["id"]

    def meta_to_exclude_from_representation(self):
        return [
            "id",
            "slug",
            "description",
            "url",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def save(self, *args, **kwargs):
        if self.id is None or not self.__class__.objects.filter(pk=self.pk).exists():
            source = getattr(self, self.get_slug_source(), None)
            if not source:
                source = getattr(self, self.get_slug_alt_source(), None)
            if source:
                self.slug = slugify(source)
                self._ensure_unique_slug()

        super().save(*args, **kwargs)

    def _ensure_unique_slug(self):
        original_slug = self.slug
        count = 1

        while self.__class__.objects.filter(slug=self.slug).exists():
            self.slug = f"{original_slug}-{count}"
            count += 1

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class BaseModel(CommonModel):
    tags = models.ManyToManyField("timbrel.Tag", blank=True)
    facetvalues = models.ManyToManyField("timbrel.FacetValue", blank=True)
    files = models.ManyToManyField("timbrel.File", blank=True)
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class BaseSerializer(serializers.ModelSerializer):
    absolute_url = serializers.SerializerMethodField(read_only=True)
    relative_url = serializers.SerializerMethodField(read_only=True)

    def to_representation(self, instance):
        from .utils import is_relationship, get_serializer_dict

        withs = []

        if "request" in self.context:
            request = self.context["request"]
            query_params = request.query_params
            with_query_params = query_params.get("with", None)
            if with_query_params:
                withs += with_query_params.split(",")

        with_context = self.context.get("with", None)
        if with_context:
            withs += with_context.split(",")

        """
        Modify the serialized data representation.
        """
        data = super().to_representation(instance)  # Get the default representation.

        # remove fields from exclude_from_representation
        for field in instance.exclude_from_representation():
            data.pop(field, None)

        # add fields from include_in_representation
        for field in instance.include_in_representation():
            data[field] = getattr(instance, field)

        serializer_dict = get_serializer_dict()

        # TODO: Kigathi - November 28 2024 - Optimize the below for loop

        model_class = instance.__class__
        for field_name in list(data.keys()):
            if is_relationship(model_class, field_name):
                data.pop(field_name, None)
                if withs and field_name in withs:
                    field = model_class._meta.get_field(field_name)
                    model_name_lower = model_class.__name__.lower()

                    through_model = None

                    if isinstance(field, ManyToManyField):
                        if (
                            field.remote_field.through
                            and not field.remote_field.through._meta.auto_created
                        ):
                            through_model = field.remote_field.through

                    is_plural = p.singular_noun(field_name)

                    related_objects = (
                        getattr(instance, field_name).all()
                        if is_plural
                        else getattr(instance, field_name)
                    )

                    singular_field = (
                        p.singular_noun(field_name) if is_plural else field_name
                    )
                    serializer_class = serializer_dict.get(singular_field)
                    if serializer_class:
                        related_data = serializer_class(
                            related_objects,
                            many=True if is_plural else False,
                            context=self.context,
                        ).data
                        #: TODO: Kigathi - November 28 2024 - Add a query_param `meta` to optionally include this meta data
                        if is_plural and through_model:
                            for data_item in related_data:
                                filter_conditions = {
                                    singular_field: data_item["id"],
                                    model_name_lower: instance,
                                }
                                through_data = through_model.objects.filter(
                                    **filter_conditions
                                ).first()
                                if through_data:
                                    through_data_dict = {
                                        f.name: getattr(through_data, f.name)
                                        for f in through_model._meta.get_fields()
                                        if (
                                            not isinstance(
                                                f,
                                                (
                                                    ForeignKey,
                                                    ManyToManyField,
                                                    OneToOneField,
                                                    ManyToOneRel,
                                                    OneToOneRel,
                                                    ManyToManyRel,
                                                ),
                                            )
                                            and (
                                                hasattr(
                                                    through_model,
                                                    "meta_to_exclude_from_representation",
                                                )
                                                and f.name
                                                not in through_model.meta_to_exclude_from_representation(
                                                    through_model
                                                )
                                            )
                                        )  # Exclude relationship fields
                                    }
                                    data_item["meta"] = through_data_dict
                        data[field_name] = related_data

        # remove field if is null or empty array or empty string
        for field, value in list(data.items()):
            if value is None or value == [] or value == "":
                data.pop(field, None)

        return data

    def get_absolute_url(self, obj):
        if hasattr(obj, "get_absolute_url") and callable(
            getattr(obj, "get_absolute_url")
        ):
            return obj.get_absolute_url()
        return None

    def get_relative_url(self, obj):
        if hasattr(obj, "get_relative_url") and callable(
            getattr(obj, "get_relative_url")
        ):
            return obj.get_relative_url()
        return None


class BaseViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        queryset = self.queryset
        query_params = self.request.query_params

        for param, value in query_params.items():
            try:
                field = self.queryset.model._meta.get_field(param)
                if field and field.many_to_many:
                    values = value.split(",")
                    # TODO: Kigathi - December 4 2024 - Ensure that the lookup field matches the many-to-many field, i.e. in the below, we assume the many-to-many field is called contains `name`
                    # TODO: Kigathi - December 4 2024 - Convert this to a search functionality instead of an exact lookup
                    queryset = queryset.filter(
                        **{f"{param}__name__in": values}
                    ).distinct()
            except FieldDoesNotExist:
                if not param.startswith("h"):
                    continue

                hierachicals = value.split(",")
                for h in hierachicals:
                    current_h = queryset.filter(name=h).first()
                    if current_h:
                        try:
                            queryset = getattr(current_h, param[1:])
                        except AttributeError:
                            continue

        return queryset


# TODO: Kigathi - November 28 2024 - Implement an all fields search filter
"""
Custom filters can be implemented, for example, 
 - a range filter that takes a column and the lower and upper bounds as parameters.
 - confirm that relationship filters work without further configuration.

field_names = [field.name for field in MyModel._meta.get_fields()]
print(field_names)
"""

# class BaseFilter(filters.FilterSet):
#     min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
#     max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')

#     def get_filterset(self, request, queryset, view):


#     class Meta:
#         abstract = True
#         fields = ['category', 'in_stock']
