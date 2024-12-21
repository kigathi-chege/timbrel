from typing import Any
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from cities_light.admin import (
    CountryAdmin as BaseCountryAdmin,
    RegionAdmin as BaseRegionAdmin,
    CityAdmin as BaseCityAdmin,
    SubRegionAdmin as BaseSubRegionAdmin,
)
from cities_light.models import Country, Region, City, SubRegion

from .models import (
    Setting,
    Tag,
    File,
    Facet,
    FacetValue,
    Advertisement,
    Article,
)
from .forms import FileAdminForm, EditFileAdminForm

from timbrel.admin import BaseAdmin


@admin.register(Setting)
class SettingAdmin(BaseAdmin):
    filter_horizontal = ("tags", "files", "facetvalues")


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    fields = (
        "name",
        "url",
    )
    search_fields = ["name"]


@admin.register(File)
class FileAdmin(BaseAdmin):
    def display_tag(self, obj):
        """
        This method is used to generate an image preview for the file.
        Ensure that the `file` field is an `ImageField` or `FileField`.
        """
        mime_type = obj.mimetype

        # TODO: Kigathi - December 19 2024 - Without mimetype assumes that the file is an image
        if not mime_type or mime_type.startswith("image"):
            return format_html(
                '<a class="flex items-center gap-2" href={} target="_blank"><img src="{}" style="max-width:200px; max-height:200px" /></a>'.format(
                    obj.url, obj.url
                )
            )
        else:
            return format_html(
                '<a class="flex items-center gap-2" href={} target="_blank"><span class="material-symbols-outlined">description</span> {}</a>'.format(
                    obj.url,
                    obj.name,
                )
            )

    display_tag.short_description = "Display"
    list_display = [
        "name",
        "size",
        "usagecount",
        "viewed_at",
        "display_tag",
    ]
    search_fields = ("name", "description")

    def get_form(
        self, request: Any, obj: Any | None = ..., change: bool = ..., **kwargs: Any
    ) -> Any:
        if obj:
            return EditFileAdminForm
        return FileAdminForm


@admin.register(Facet)
class FacetAdmin(BaseAdmin):
    search_fields = ["name"]
    fields = ("name", "tags")
    filter_horizontal = ("tags",)


@admin.register(FacetValue)
class FacetValueAdmin(BaseAdmin):
    search_fields = ["name"]
    fields = ("name", "facet", "tags")
    filter_horizontal = ["tags"]


@admin.register(Advertisement)
class AdvertisementAdmin(BaseAdmin):
    search_fields = ["title"]
    fields = (
        "title",
        "ad_type",
        "start_time",
        "end_time",
        "user",
    )
    autocomplete_fields = ["user"]


@admin.register(Article)
class ArticleAdmin(BaseAdmin):
    search_fields = ["title"]
    fields = ("title", "content")
    filter_horizontal = ["tags", "files", "facetvalues"]


admin.site.unregister(Country)
admin.site.unregister(Region)
admin.site.unregister(SubRegion)
admin.site.unregister(City)


@admin.register(Country)
class CountryAdmin(BaseCountryAdmin, BaseAdmin):
    pass


@admin.register(Region)
class RegionAdmin(BaseRegionAdmin, BaseAdmin):
    pass


@admin.register(SubRegion)
class SubRegionAdmin(BaseSubRegionAdmin, BaseAdmin):
    pass


@admin.register(City)
class CityAdmin(BaseCityAdmin, BaseAdmin):
    pass
