from django.db import models
from django.utils import timezone
from django.utils import timezone
from simple_history.models import HistoricalRecords

from timbrel.base import CommonModel, BaseModel

from timbrel.uicopy.models import (
    Text,
    Image,
)


class Setting(BaseModel):
    name = models.CharField()
    value = models.TextField(null=True, blank=True)


class Tag(BaseModel):
    name = models.CharField(unique=True)

    def __str__(self):
        return self.name


class Facet(CommonModel):
    name = models.CharField(unique=True)
    tags = models.ManyToManyField("timbrel.Tag", blank=True)
    history = HistoricalRecords(inherit=True)

    def __str__(self):
        return self.name


class FacetValue(CommonModel):
    name = models.CharField()
    facet = models.ForeignKey(
        Facet, on_delete=models.CASCADE, related_name="facetvalues"
    )
    tags = models.ManyToManyField("timbrel.Tag", blank=True)
    history = HistoricalRecords(inherit=True)

    def __str__(self):
        return f"{self.facet.name} - {self.name}"


class File(BaseModel):
    name = models.CharField(max_length=200)
    path = models.TextField(null=True, blank=True)
    size = models.IntegerField(default=0)
    extension = models.CharField(max_length=10, null=True, blank=True)
    mimetype = models.CharField(max_length=100, null=True, blank=True)
    usagecount = models.IntegerField(default=1)
    checksum = models.CharField(max_length=100, null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name


class Advertisement(BaseModel):
    BIG = "big"
    SMALL = "small"
    AD_TYPE_CHOICES = [
        (BIG, "Big"),
        (SMALL, "Small"),
    ]

    ad_type = models.CharField(
        max_length=10,
        choices=AD_TYPE_CHOICES,
        default=SMALL,
    )
    start_time = models.DateTimeField(help_text="When the advertisement starts")
    end_time = models.DateTimeField(help_text="When the advertisement ends")
    user = models.ForeignKey(
        "timbrel.User",
        on_delete=models.CASCADE,
        related_name="advertisements",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_ad_type_display()})"

    @property
    def advertisement_status(self, *args, **kwargs):
        if self.end_time < timezone.now():
            return "expired"
        elif self.start_time > timezone.now():
            return "inactive"
        else:
            return "active"

    @property
    def is_active(self):
        return self.advertisement_status == "active"


class Article(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ArticleText(BaseModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]


class ArticleImage(BaseModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
