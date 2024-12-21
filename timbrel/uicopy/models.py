from django.db import models
from django.contrib.contenttypes.models import ContentType


from timbrel.base import BaseModel


class Text(BaseModel):
    content = models.TextField(null=True, blank=True)
    link = models.CharField(null=True, blank=True)

    def __str__(self):
        return self.content


class Button(BaseModel):
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    link = models.CharField(null=True, blank=True)

    def __str__(self):
        return self.text.content


class Image(BaseModel):
    title = models.CharField(max_length=200)
    link = models.CharField(null=True, blank=True)
    is_svg = models.BooleanField(default=False)
    svg_content = models.TextField(null=True, blank=True)
    alt = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title


class Data(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    filters = models.JSONField(null=True, blank=True)


class Section(BaseModel):
    title = models.CharField(max_length=200, unique=True)
    children = models.ManyToManyField("self", blank=True, through="SectionSection")
    texts = models.ManyToManyField(Text, blank=True, through="SectionText")
    buttons = models.ManyToManyField(Button, blank=True, through="SectionButton")
    images = models.ManyToManyField(Image, blank=True, through="SectionImage")
    data = models.ManyToManyField(Data, blank=True, through="SectionData")

    def __str__(self):
        return self.title


class SectionSection(BaseModel):
    parent = models.ForeignKey(
        Section, related_name="parent_sections", on_delete=models.CASCADE
    )
    child = models.ForeignKey(
        Section, related_name="child_sections", on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        unique_together = ("parent", "child")

    def __str__(self):
        return f"{self.parent} -> {self.child}"


class Page(BaseModel):
    title = models.CharField(max_length=200, unique=True)
    content = models.TextField(null=True, blank=True)
    sections = models.ManyToManyField(Section, blank=True, through="PageSection")
    meta_description = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    canonical_url = models.URLField(blank=True, null=True)
    og_title = models.CharField(max_length=60, blank=True, null=True)
    og_description = models.TextField(blank=True, null=True)
    og_image = models.ImageField(upload_to="og_images/", blank=True, null=True)
    twitter_title = models.CharField(max_length=60, blank=True, null=True)
    twitter_description = models.TextField(blank=True, null=True)
    twitter_image = models.ImageField(
        upload_to="twitter_images/", blank=True, null=True
    )
    schema_markup = models.JSONField(blank=True, null=True)
    robots_meta_tag = models.CharField(max_length=10, default="index")
    total_views = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class SectionText(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]


class SectionButton(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    button = models.ForeignKey(Button, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]


class SectionImage(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]


class PageSection(BaseModel):
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.page.title} - {self.section.title}"

    class Meta:
        ordering = ["order"]


class SectionData(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    data = models.ForeignKey(Data, on_delete=models.CASCADE, null=True, blank=True)
