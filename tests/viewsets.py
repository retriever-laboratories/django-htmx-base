# viewsets
from django_htmx_base.viewsets import HtmxViewSet

# forms
from tests.forms import TestForm

# models
from tests.models import TestBaseModel
from tests.models import TestBaseModelUserTracked


class TestBaseModelViewSet(HtmxViewSet):
    model = TestBaseModel


class TestCustomFormViewSet(HtmxViewSet):
    model = TestBaseModel
    form_class = TestForm


class TestBaseModelUserTrackedViewSet(HtmxViewSet):
    model = TestBaseModelUserTracked
