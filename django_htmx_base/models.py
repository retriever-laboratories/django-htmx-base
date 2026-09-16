# standard
import csv
from enum import StrEnum
from io import StringIO

# django
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class FilterInputType(StrEnum):
    CHECKBOX = "checkbox"
    DATE = "date"
    DATETIME_LOCAL = "datetime-local"
    MULTISELECT = "multiselect"
    NUMBER = "number"
    RADIO = "radio"
    RANGE = "range"
    SELECT = "select"
    TEXT = "text"
    TIME = "time"


def BaseField(base_field_class, **kwargs):  # noqa: N802
    sortable = kwargs.pop("sortable", False)
    partial = kwargs.pop("partial", None)
    css_class = kwargs.pop("css_class", "")
    filtrable = kwargs.pop("filtrable", False)
    unique_order_attribute = kwargs.pop("unique_order_attribute", False)
    filter_input_type = FilterInputType(
        kwargs.pop("filter_input_type", FilterInputType.TEXT)
    )

    field = base_field_class(**kwargs)
    field.sortable = sortable
    field.partial = partial
    field.css_class = css_class
    field.filtrable = filtrable
    field.unique_order_attribute = unique_order_attribute
    field.filter_input_type = filter_input_type

    return field


class BaseModel(models.Model):
    """
    Abstract base for all models
    """

    # fields
    created_at = BaseField(models.DateTimeField, auto_now_add=True, sortable=True)
    updated_at = BaseField(models.DateTimeField, auto_now=True, sortable=True)
    created_by = BaseField(
        models.ForeignKey,
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created_set",
        filtrable=True,
    )
    updated_by = BaseField(
        models.ForeignKey,
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated_set",
        filtrable=True,
    )
    is_active = BaseField(
        models.BooleanField,
        default=True,
        filtrable=True,
        filter_input_type=FilterInputType.SELECT,
    )

    # view attributes
    _display_fields = ["id", "created_at", "is_active"]
    _downloadable = True

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={getattr(self, 'id', None)})"

    def delete(self, *args, **kwargs):
        if getattr(settings, "SOFT_DELETE", False):
            return self.soft_delete()

        return super().delete(*args, **kwargs)

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def restore(self):
        self.is_active = True
        self.save(update_fields=["is_active"])

    @classmethod
    def get_filtrable_fields(cls):
        """
        Returns context-ready filter metadata for each filtrable field.
        """
        return [
            field
            for field in cls.get_display_fields()
            if getattr(field, "filtrable", False)
        ]

    @classmethod
    def get_filters_objects(cls):
        filters = []

        for field in cls.get_filtrable_fields():
            filter_config = {
                "field": field.name,
                "filter_input_type": getattr(
                    field, "filter_input_type", FilterInputType.TEXT
                ).value,
            }

            if hasattr(field, "choices") and field.choices:
                filter_config["options"] = [
                    {"value": value, "label": label}
                    for value, label in field.choices
                    if value not in (None, "")
                ]
            elif isinstance(field, models.BooleanField):
                filter_config["options"] = [
                    {"value": "True", "label": "True"},
                    {"value": "False", "label": "False"},
                ]

            filters.append(filter_config)

        return filters

    @property
    def filters(self):
        return self.get_filtrable_fields()

    @property
    def filters_objects(self):
        return self.get_filters_objects()

    @classmethod
    def sortable_fields(cls):
        """
        Returns a list of fields that are sortable.
        """
        return [
            field.name
            for field in cls.get_display_fields()
            if getattr(field, "sortable", False)
        ]

    @classmethod
    def get_display_fields(cls):
        return [cls._meta.get_field(x) for x in cls._display_fields]

    @property
    def display_fields(self):
        return self.get_display_fields()

    def as_list(self):
        """Ordered values for this instance, matching ``display_fields`` order."""
        values = []
        for field in self.display_fields:
            if getattr(field, "choices", None):
                value = getattr(self, f"get_{field.name}_display")()
            else:
                value = getattr(self, field.name)

            values.append(value)

        return values

    def as_field_values_objects_list(self):
        """Ordered cells for this instance, matching ``display_fields`` order."""
        field_objects = []

        for field in self.display_fields:
            if getattr(field, "choices", None):
                value = getattr(self, f"get_{field.name}_display")()
            else:
                value = getattr(self, field.name)

            field_objects.append(
                {
                    "field": field.name,
                    "value": value,
                    "partial": getattr(field, "partial", None),
                    "class": getattr(field, "css_class", ""),
                }
            )

        return field_objects

    @classmethod
    def to_csv(cls, queryset):
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(field.name for field in cls.get_display_fields())

        for object in queryset:
            writer.writerow(object.as_list())

        return output.getvalue()

    @classmethod
    def as_field_names_objects_list(cls):
        columns = []

        for field in cls.get_display_fields():
            column = {
                "field": field.name,
                "sortable": getattr(field, "sortable", False),
                "filtrable": getattr(field, "filtrable", False),
            }

            partial = getattr(field, "partial", None)
            if partial:
                column["partial"] = partial

            css_class = getattr(field, "css_class", None)
            if css_class:
                column["class"] = css_class

            columns.append(column)

        return columns

    @classmethod
    def is_downloadable(cls):
        return cls._downloadable


class BaseOrderIndexModel(BaseModel):
    order_index = BaseField(
        models.PositiveIntegerField,
        null=True,
    )

    class Meta:
        abstract = True
        ordering = ("order_index",)
        constraints = []

        def __init__(self, *args, **kwargs):
            for unique_attr in BaseOrderIndexModel.get_unique_order_attributes():
                self.constraints.append(
                    models.UniqueConstraint(
                        fields=[unique_attr, "order_index"],
                        name=f"{unique_attr}_order_index_constraint",
                    ),
                )

            return super().__init__(*args, **kwargs)

    @classmethod
    def last_index(cls, **query_kwargs):
        last_obj = cls.objects.filter(**query_kwargs).last()

        return last_obj.order_index if last_obj else None

    def next_index(self, **query_kwargs):
        if not query_kwargs:
            query_kwargs = self.get_query_kwargs()

        last_index = self.last_index(**query_kwargs)

        return last_index + 1 if last_index is not None else 0

    @property
    def unique_order_attributes(self):
        return self.get_unique_order_attributes()

    @classmethod
    def get_unique_order_attributes(cls):
        """
        Returns a list of fields that are unique order attributes.
        """
        return [
            field.name
            for field in cls._meta.fields
            if getattr(field, "unique_order_attribute", False)
        ]

    def get_query_kwargs(self):
        return {k: getattr(self, k, None) for k in self.get_unique_order_attributes()}

    def update_order_index(self, order_index):
        elements = list(
            self.__class__.objects.filter(**self.get_query_kwargs()).exclude(pk=self.pk)
        )
        elements.insert(order_index, self)

        for index, element in enumerate(elements):
            element.order_index = index

        self.__class__.objects.bulk_update(elements, ["order_index"])

        return self

    def save(self, *args, **kwargs):
        query_kwargs = kwargs.get("query_kwargs") or {}
        if self.order_index is None:
            self.order_index = self.next_index(**query_kwargs)

        self.clean_order_uniqueness(**query_kwargs)

        super().save(*args, **kwargs)

    def clean_order_uniqueness(self, **query_kwargs):
        query_kwargs = query_kwargs or self.get_query_kwargs()

        if not query_kwargs:
            return

        query_kwargs.update({"order_index": self.order_index})

        for unique_attr in self.__class__.get_unique_order_attributes():
            if self.__class__.objects.filter(**query_kwargs).exists():
                raise ValidationError(
                    f"Order index {self.order_index} already exists for {unique_attr}"
                )
