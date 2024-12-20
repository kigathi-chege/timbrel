from typing import Any
from django.db import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from cities_light.admin import (
    CountryAdmin as BaseCountryAdmin,
    RegionAdmin as BaseRegionAdmin,
    CityAdmin as BaseCityAdmin,
    SubRegionAdmin as BaseSubRegionAdmin,
)
from cities_light.models import Country, Region, City, SubRegion
from simple_history.admin import SimpleHistoryAdmin

from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget

from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import (
    ExportForm,
    ImportForm,
    SelectableFieldsExportForm,
)


from .models import Order, Transaction, Coupon
from .inlines import OrderProductsInline

from .models import (
    Setting,
    Tag,
    File,
    Facet,
    FacetValue,
    Advertisement,
    Article,
    Page,
    Section,
    Text,
    Button,
    Image,
    User,
    Product,
    Store,
    Offer,
)
from .forms import FileAdminForm, EditFileAdminForm
from .inlines import (
    FileInline,
    TagInline,
    FacetValueInline,
    PageSectionInline,
    TextInline,
    ImageInline,
    ButtonInline,
    SectionSectionInline,
    create_dynamic_inline,
)


class BaseAdmin(ModelAdmin, SimpleHistoryAdmin, ImportExportModelAdmin):
    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        }
    }
    import_form_class = ImportForm
    export_form_class = ExportForm
    export_form_class = SelectableFieldsExportForm

    def __init__(self, *args, **kwargs):
        """
        Initialize BaseAdmin, dynamically generate inlines based on the model's fields.
        """
        super().__init__(*args, **kwargs)

        # Initialize inlines list dynamically
        self.inlines = []

        # Check if the model has 'files', 'tags', 'facetvalues', and create inlines for them
        for field in self.model._meta.get_fields():
            if isinstance(field, models.ManyToManyField):
                if field.name == "files":
                    inline_class = FileInline
                elif field.name == "tags":
                    inline_class = TagInline
                elif field.name == "facetvalues":
                    inline_class = FacetValueInline
                else:
                    continue  # Skip other ManyToManyFields if necessary

                dynamic_inline = create_dynamic_inline(
                    inline_class, self.model, field.name
                )
                self.inlines.append(dynamic_inline)

        if hasattr(self, "custom_inlines"):
            # Insert custom inlines at the beginning of the list
            self.inlines = self.custom_inlines + self.inlines

    pass


"""ACCOUNT ADMIN"""


@admin.register(User)
class UserAdmin(BaseUserAdmin, BaseAdmin):
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    ("username", "email"),
                    ("first_name", "last_name"),
                    "description",
                    "url",
                    "newsletter",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, BaseAdmin):
    pass


"""INVENTORY ADMIN"""


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    fields = (
        ("name", "price"),
        ("sku", "stock_level"),
        "is_saleable",
        "url",
        "offer",
        "description",
    )

    list_display = (
        "name",
        "price",
        "sku",
        "stock_level",
    )
    search_fields = ("name", "description", "url", "sku")
    readonly_fields = ("sku",)
    autocomplete_fields = ("offer",)


@admin.register(Store)
class StoreAdmin(BaseAdmin):
    fields = (
        "name",
        "phone",
        "email",
        "longitude",
        "latitude",
        "description",
        "url",
        "users",
    )
    list_display = ("name", "phone")
    search_fields = ("name", "phone")
    filter_horizontal = ("users",)


@admin.register(Offer)
class OfferAdmin(BaseAdmin):
    fields = (
        "name",
        "discount",
        "is_percentage",
        "valid_from",
        "valid_to",
        "description",
        "url",
    )
    list_display = ("name", "discount", "is_percentage", "valid_from", "valid_to")
    search_fields = ("name",)


"""PAYMENT MODEL"""


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    fieldsets = [
        (
            _("Order Information"),
            {
                "fields": [
                    "user",
                    ("reference", "total_amount", "order_status"),
                    "description",
                ],
                "classes": ["tab"],
            },
        ),
        (
            _("Delivery Information"),
            {
                "fields": (
                    ("delivery_method", "delivery_address"),
                    ("delivery_latitude", "delivery_longitude"),
                    ("delivery_charges", "packaging_cost"),
                ),
                "classes": ["tab"],
            },
        ),
        (
            _("More Details"),
            {
                "fields": (
                    "coupon",
                    "coupon_applied",
                    ("promotional_discount", "custom_discount"),
                ),
                "classes": ["tab"],
            },
        ),
    ]
    readonly_fields = ["user", "reference", "total_amount"]
    list_display = ("user", "reference", "created_at", "total_amount", "order_status")
    search_fields = ["reference"]
    custom_inlines = [OrderProductsInline]


@admin.register(Transaction)
class TransactionAdmin(BaseAdmin):
    fields = (
        "user",
        "reference",
        ("amount", "balance"),
        ("transaction_type", "transaction_status"),
        "order",
        "payment_method",
        "description",
    )
    list_display = (
        "user",
        "reference",
        "amount",
        "transaction_type",
        "transaction_status",
    )
    readonly_fields = [
        "user",
        "reference",
        "amount",
        "order",
        "balance",
        "transaction_type",
        "transaction_status",
        "payment_method",
    ]
    search_fields = ["reference"]


@admin.register(Coupon)
class CouponAdmin(BaseAdmin):
    fields = [
        ("code", "discount"),
        "is_percentage",
        "valid_from",
        "valid_to",
        ("usage_limit", "used_count"),
        "active",
    ]
    list_display = [
        "code",
        "discount",
        "is_percentage",
        "valid_from",
        "valid_to",
        "usage_limit",
        "used_count",
        "active",
    ]
    readonly_fields = ["code"]
    list_filter = ["active", "valid_from", "valid_to"]
    search_fields = ["code"]
    filter_horizontal = ("tags", "files", "facetvalues")


"""COMMON ADMIN"""


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


# from django.utils.translation import ugettext as _
# from django.contrib.admin.widgets import AdminFileWidget
# from django.utils.safestring import mark_safe


# class AdminImageWidget(AdminFileWidget):
#     def render(self, name, value, attrs=None, renderer=None):
#         output = []
#         if value and getattr(value, "url", None):
#             image_url = value.url
#             file_name = str(value)
#             output.append(u' <a href="%s" target="_blank"><img src="%s" alt="%s" /></a> %s ' % \
#                       (image_url, image_url, file_name, 'Change:'))
#         output.append(super(AdminFileWidget, self).render(name, value, attrs, renderer))
#         return mark_safe(u''.join(output))


# class UploadedImagePreview(object):
#     short_description = _('Thumbnail')
#     allow_tags = True

#     def __init__(self, image_field, template, short_description=None, width=None, height=None):
#         self.image_field = image_field
#         self.template = template
#         if short_description:
#             self.short_description = short_description
#         self.width = width or 200
#         self.height = height or 200

#     def __call__(self, obj):
#         try:
#             image = getattr(obj, self.image_field)
#         except AttributeError:
#             raise Exception('The property %s is not defined on %s.' %
#                 (self.image_field, obj.__class__.__name__))

#         template = self.template

#         return render_to_string(template, {
#             'width': self.width,
#             'height': self.height,
#             'watch_field_id': 'id_' + self.image_field  # id_<field_name> is default ID
#                                                         # for ImageField input named `<field_name>` (in Django Admin)
#         })


# @admin.register(File)
# class MainPageBannerAdmin(ModelAdmin):
#     image_preview = UploadedImagePreview(image_field='image', template='admin/image_preview.html',
#                                          short_description='uploaded image', width=245, height=245)
#     readonly_fields = ('image_preview',)

#     fields = (('image', 'image_preview'), 'title')


"""UICOPY ADMIN"""

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
