# standard
import csv
from enum import StrEnum
from io import StringIO
from typing import cast

# django
from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import F
from django.db.models import Max
from django.db.models.base import ModelBase


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


class OrderIndexModelBase(ModelBase):
    def __new__(mcls, name, bases, attrs, **kwargs):
        cls = cast(type[BaseModel], super().__new__(mcls, name, bases, attrs, **kwargs))

        if cls._meta.abstract:
            return cls

        constraint = cls.get_order_index_constraint()  # type: ignore[attr-defined]

        if constraint is None:
            return cls

        cls._meta.constraints = (
            *cls._meta.constraints,
            constraint,
        )

        cls._meta.original_attrs["constraints"] = list(cls._meta.constraints)

        return cls


class BaseOrderIndexModel(BaseModel, metaclass=OrderIndexModelBase):
    """
    Provides contiguous, zero-based ordering within each ordering group
    when instances are saved.

    The ordering group is determined by all fields marked with
    ``unique_order_attribute=True``. Objects are ordered by ``order_index``.

    When saving:

    - ``None`` → append at the end.
    - Explicit index on a new object → insert at that position.
    - Existing object moved down → shift intervening items up.
    - Existing object moved up → shift intervening items down.
    - Index beyond the end → clamp to the end.
    - Moving to the same index → do nothing.

    The ordering is maintained atomically during save, so a reorder and the
    object save are committed or rolled back together.
    """

    order_index = BaseField(
        models.PositiveIntegerField,
        null=True,
    )

    class Meta:
        abstract = True
        ordering = ("order_index",)

    @classmethod
    def get_order_index_constraint(cls):
        attributes = cls.get_unique_order_attributes()

        if not attributes:
            return None

        constraint_name = f"{cls._meta.app_label}_{cls._meta.model_name}_order_index"

        return models.UniqueConstraint(
            fields=[*attributes, "order_index"],
            name=constraint_name,
            deferrable=models.Deferrable.DEFERRED,
        )

    def last_index(self):
        filter_kwargs = self.get_filter_kwargs()

        return self.__class__.objects.filter(**filter_kwargs).aggregate(
            max_index=Max("order_index")
        )["max_index"]

    def next_index(self):
        last_index = self.last_index()

        return last_index + 1 if last_index is not None else 0

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

    def get_filter_kwargs(self):
        return {
            field: getattr(self, field) for field in self.get_unique_order_attributes()
        }

    def shift_order_indexes(self, old_index):
        if self.order_index == old_index:
            return

        filter_kwargs = self.get_filter_kwargs()
        objs = self.__class__.objects.filter(**filter_kwargs)

        if old_index is None:
            objs.filter(
                order_index__gte=self.order_index,
            ).update(order_index=F("order_index") + 1)
        elif self.order_index < old_index:
            objs.filter(
                order_index__gte=self.order_index,
                order_index__lt=old_index,
            ).exclude(pk=self.pk).update(order_index=F("order_index") + 1)
        else:
            objs.filter(
                order_index__gt=old_index,
                order_index__lte=self.order_index,
            ).exclude(pk=self.pk).update(order_index=F("order_index") - 1)

    def clean_order_index(self):
        next_index = self.next_index()
        old_index = None

        if self.pk:
            old_index = (
                self.__class__.objects.filter(pk=self.pk)
                .values_list("order_index", flat=True)
                .first()
            )

        if self.order_index is None:
            self.order_index = next_index
            return

        max_index = next_index - 1 if old_index is not None else next_index
        self.order_index = min(self.order_index, max_index)

        if old_index != self.order_index:
            self.shift_order_indexes(old_index)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.clean_order_index()
            super().save(*args, **kwargs)
