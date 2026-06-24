from enum import StrEnum

from django.db import models


class FilterInputType(StrEnum):
    TEXT = "text"
    SELECT = "select"


def BaseField(base_field_class, **kwargs):  # noqa: N802

    sortable = kwargs.pop("sortable", False)
    partial = kwargs.pop("partial", "default")
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
    display_fields = ("id", "created_at", "is_active")

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={getattr(self, 'id', None)})"

    @classmethod
    def filtrable_fields(cls):
        """
        Returns context-ready filter metadata for each filtrable field.
        """
        filters = []

        for field in cls._meta.get_fields():
            if not getattr(field, "filtrable", False):
                continue

            filter_config = {
                "field": field.name,
                "filter_input_type": getattr(
                    field, "filter_input_type", FilterInputType.TEXT
                ).value,
            }

            if field.choices:
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
        return self.filtrable_fields()

    @classmethod
    def sortable_fields(cls):
        """
        Returns a list of fields that are sortable.
        """
        return [
            field.name
            for field in cls._meta.get_fields()
            if getattr(field, "sortable", False)
        ]

    @classmethod
    def table_columns(cls):
        return [
            cls._get_table_column(field)
            for field in cls._meta.get_fields()
            if field.name in cls.display_fields
        ]

    @property
    def columns(self):
        return self.table_columns()

    @classmethod
    def _get_table_column(cls, field):
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

        return column
