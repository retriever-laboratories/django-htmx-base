# django
from django import forms

# boundfield
from django_htmx_base.boundfield import CustomBoundField

# mixins
from django_htmx_base.mixins import DisplayOnlyMixin
from django_htmx_base.mixins import WidgetStylerMixin


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
