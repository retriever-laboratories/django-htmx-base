# django
from django.forms.boundfield import BoundField


class CustomBoundField(BoundField):
    @property
    def is_display_only(self):
        return getattr(self.field.widget, 'is_display_only', False)
