# django
from django import forms

from django_htmx_base.mixins import DisplayOnlyMixin

# mixins
from django_htmx_base.mixins import WidgetStylerMixin

# boundfield
from django_htmx_base.boundfield import CustomBoundField


class BaseForm(WidgetStylerMixin, DisplayOnlyMixin, forms.Form):
    bound_field_class = CustomBoundField
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_styles()


class BaseModelForm(WidgetStylerMixin, DisplayOnlyMixin, forms.ModelForm):
    bound_field_class = CustomBoundField
    class Meta:
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_styles()
