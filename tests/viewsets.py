# django
from django.forms import BaseModelFormSet
from django.http import HttpResponse

# viewsets
from django_htmx_base.viewsets import HtmxViewSet
from django_htmx_base.viewsets import action

# forms
from tests.forms import TestForm

# models
from tests.models import TestBaseModel


class TestBaseModelViewSet(HtmxViewSet):
    model = TestBaseModel


class TestCustomFormViewSet(HtmxViewSet):
    model = TestBaseModel
    form_class = TestForm


class TestCustomFormSetViewSet(HtmxViewSet):
    model = TestBaseModel
    formset = BaseModelFormSet


class TestToastViewSet(HtmxViewSet):
    model = TestBaseModel

    @action(methods=["post"], detail=False)
    def lets_make_a_toast(self, request):  # noqa: ARG002
        self.add_toast("Toast is actually a bread reference")

        return HttpResponse("<div>Cheers!</div>")
