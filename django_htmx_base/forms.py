# django
from django import forms

# widgets
from base.widgets import WidgetStylerMixin


class BaseForm(WidgetStylerMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_styles()


class BaseModelForm(WidgetStylerMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_styles()
