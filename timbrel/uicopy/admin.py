from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from timbrel.admin import BaseAdmin

from .models import (
    Page,
    Section,
    Text,
    Button,
    Image,
)
from .inlines import (
    PageSectionInline,
    TextInline,
    ImageInline,
    ButtonInline,
    SectionSectionInline,
)


# class FlatPageAdmin(FlatPageAdmin, ModelAdmin):
#     fieldsets = [
#         (None, {"fields": ["url", "title", "content", "sites"]}),
#         (
#             _("Advanced options"),
#             {
#                 "classes": ["collapse"],
#                 "fields": [
#                     "enable_comments",
#                     "registration_required",
#                     "template_name",
#                 ],
#             },
#         ),
#     ]


# Re-register FlatPageAdmin
# admin.site.unregister(FlatPage)
# admin.site.register(FlatPage, FlatPageAdmin)


@admin.register(Page)
class PageAdmin(BaseAdmin):
    fields = ["title", "description", "url", "content", "meta_description", "keywords"]
    list_display = ("title",)
    search_fields = ("title",)
    custom_inlines = [PageSectionInline]
    exclude = ("sections",)


@admin.register(Section)
class SectionAdmin(BaseAdmin):
    fields = ["title", "description", "url"]
    list_display = ["title"]
    search_fields = ["title"]
    custom_inlines = [TextInline, ImageInline, ButtonInline, SectionSectionInline]


@admin.register(Text)
class TextAdmin(BaseAdmin):
    fields = ["content", "link", "description", "url"]
    list_display = ("content", "link")
    search_fields = ("content", "link")


@admin.register(Button)
class ButtonAdmin(BaseAdmin):
    list_display = ("text", "link")
    search_fields = ("text", "link")


@admin.register(Image)
class ImageAdmin(BaseAdmin):
    list_display = ("title", "link")
    search_fields = ("title", "link")
