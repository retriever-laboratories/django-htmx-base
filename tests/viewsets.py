from django_htmx_base.viewsets import HtmxViewSet
from tests.models import TestBaseModel


class TestBaseModelViewSet(HtmxViewSet):
    model = TestBaseModel
