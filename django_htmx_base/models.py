# standard
import csv
from enum import StrEnum
from io import StringIO

# django
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
    filter_input_type = FilterInputType(
        kwargs.pop("filter_input_type", FilterInputType.TEXT)
    )

    field = base_field_class(**kwargs)
    field.sortable = sortable
    field.partial = partial
    field.css_class = css_class
    field.filtrable = filtrable
    field.filter_input_type = filter_input_type

    return field


class BaseModel(models.Model):
    """
    Abstract base for all models
    """

    # fields
    created_at = BaseField(
        models.DateTimeField, auto_now_add=True, editable=False, sortable=True
    )
    updated_at = BaseField(models.DateTimeField, auto_now=True, editable=False)
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
        return [
            field
            for field in cls._meta.get_fields()
            if field.name in cls._display_fields
        ]

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
