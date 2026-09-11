# forms
from django_htmx_base.forms import BaseModelForm

# models
from tests.models import TestBaseModel


class TestForm(BaseModelForm):
    class Meta:
        model = TestBaseModel
        fields = ["id", "test_charfield", "test_display_field"]
        display_only_fields = ["test_display_field"]
