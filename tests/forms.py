# models

# forms
from django_htmx_base.forms import BaseModelForm


class TestForm(BaseModelForm):
    class Meta:
        fields = ["id", "test_charfield"]
