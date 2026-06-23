from django.db import models


def BaseField(base_field_class, **kwargs):

    sortable = kwargs.pop("sortable", False)
    partial = kwargs.pop("partial", "default")
    css_class = kwargs.pop("css_class", "")
    filtrable = kwargs.pop("filtrable", False)
    filter_input_type = kwargs.pop("filter_input_type", "text")

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
    created_at = BaseField(models.DateTimeField, auto_now_add=True, editable=False, sortable=True, partial="datetime", css_class="created-at")
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)
        display_fields = ("id", "created_at", "is_active")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={getattr(self, 'id', None)})"
    
    @classmethod
    def filtrable_fields(self):
        """
        Returns a list of fields that are filtrable
        """
        return [field.name for field in self._meta.get_fields() if getattr(field, "filtrable", False)]
