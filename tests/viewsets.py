# viewsets
from django_htmx_base.viewsets import HtmxViewSet

# forms
from tests.forms import TestForm

# models
from tests.models import TestBaseModel


class TestBaseModelViewSet(HtmxViewSet):
    model = TestBaseModel


class TestCustomFormViewSet(HtmxViewSet):
    model = TestBaseModel
    form_class = TestForm
