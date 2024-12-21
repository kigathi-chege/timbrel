from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget

from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import (
    ExportForm,
    ImportForm,
    SelectableFieldsExportForm,
)

from .utils import import_classes, prepare_modules

from .inlines import (
    FileInline,
    TagInline,
    FacetValueInline,
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


globals().update(import_classes(prepare_modules("admin")))


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
