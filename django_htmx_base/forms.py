# django
from django import forms

from django_htmx_base.mixins import DisplayOnlyMixin

# mixins
from django_htmx_base.mixins import WidgetStylerMixin


class BaseForm(WidgetStylerMixin, DisplayOnlyMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_styles()


class BaseModelForm(WidgetStylerMixin, DisplayOnlyMixin, forms.ModelForm):
    class Meta:
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_styles()
