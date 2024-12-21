from unfold.admin import TabularInline

from .models import Page, Section


class PageSectionInline(TabularInline):
    model = Page.sections.through
    verbose_name = "section"
    fields = ["section", "order"]
    autocomplete_fields = ["section"]
    tab = True
    extra = 0
    show_change_link = False
    ordering = ["order"]


class SectionSectionInline(TabularInline):
    model = Section.children.through
    verbose_name = "section"
    fields = ["parent", "child", "order"]
    autocomplete_fields = ["parent", "child"]
    tab = True
    extra = 0
    show_change_link = False
    ordering = ["order"]
    fk_name = "parent"


class TextInline(TabularInline):
    model = Section.texts.through
    verbose_name = "text"
    fields = ["text", "order"]
    autocomplete_fields = ["text"]
    tab = True
    extra = 0
    show_change_link = False
    ordering = ["order"]


class ButtonInline(TabularInline):
    model = Section.buttons.through
    verbose_name = "button"
    fields = ["button", "order"]
    autocomplete_fields = ["button"]
    tab = True
    extra = 0
    show_change_link = False
    ordering = ["order"]


class ImageInline(TabularInline):
    model = Section.images.through
    verbose_name = "image"
    fields = ["image", "order"]
    autocomplete_fields = ["image"]
    tab = True
    extra = 0
    show_change_link = False
    ordering = ["order"]
