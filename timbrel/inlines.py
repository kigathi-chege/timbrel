from unfold.admin import TabularInline
from django.utils.html import format_html


class FileInline(TabularInline):
    verbose_name = "file"
    readonly_fields = ["display_tag"]
    list_display = ["file", "display_tag"]
    fieldsets = [(None, {"fields": ["file", "display_tag"]})]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.model.__name__ == "File_files":
            self.fk_name = "from_file"
            self.autocomplete_fields = ["from_file", "to_file"]
            self.fieldsets = [(None, {"fields": ["from_file", "to_file"]})]
            self.list_display = ["from_file", "to_file"]

    def display_tag(self, obj):
        """
        This method is used to generate an image preview for the file.
        Ensure that the `file` field is an `ImageField` or `FileField`.
        """
        if hasattr(obj, "file") and obj.file:
            mime_type = obj.file.mimetype

            # TODO: Kigathi - December 19 2024 - Without mimetype assumes that the file is an image
            if not mime_type or mime_type.startswith("image"):
                return format_html(
                    '<a class="flex items-center gap-2" href={} target="_blank"><img src="{}" style="max-width:200px; max-height:200px" /></a>'.format(
                        obj.file.url, obj.file.url
                    )
                )
            else:
                return format_html(
                    '<a class="flex items-center gap-2" href={} target="_blank"><span class="material-symbols-outlined">description</span> {}</a>'.format(
                        obj.file.url,
                        obj.file.name,
                    )
                )
        return "No image"

    display_tag.short_description = "Display"
    autocomplete_fields = ["file"]


class TagInline(TabularInline):
    verbose_name = "tag"
    list_display = ["tag"]
    fieldsets = [(None, {"fields": ["tag"]})]
    autocomplete_fields = ["tag"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.model.__name__ == "Tag_tags":
            self.fk_name = "from_tag"
            self.autocomplete_fields = ["from_tag", "to_tag"]
            self.fieldsets = [(None, {"fields": ["from_tag", "to_tag"]})]
            self.list_display = ["from_tag", "to_tag"]


class FacetValueInline(TabularInline):
    verbose_name = "facet value"
    list_display = ["facetvalue"]
    fieldsets = [(None, {"fields": ["facetvalue"]})]
    autocomplete_fields = ["facetvalue"]


def create_dynamic_inline(inline, this_model, related_field, fk_name=None):
    through_model = getattr(this_model, related_field).through

    class DynamicInline(inline):
        model = through_model
        extra = 0
        tab = True
        show_change_link = False

    if fk_name:
        DynamicInline.fk_name = fk_name

    return DynamicInline
