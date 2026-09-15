from django.db import models

from django_htmx_base.models import BaseField
from django_htmx_base.models import BaseModel
from django_htmx_base.models import BaseOrderIndexModel


class TestBaseModel(BaseModel):
    test_charfield = BaseField(models.CharField, max_length=100)
    test_display_field = BaseField(
        models.CharField, max_length=100, null=True, blank=True
    )


class TestBaseOrderIndexModel(BaseOrderIndexModel):
    test_charfield = BaseField(models.CharField, max_length=100)
    test_fk = BaseField(
        models.ForeignKey,
        to=TestBaseModel,
        on_delete=models.CASCADE,
    )


class TestBaseOrderIndexModelUniqueAttr(BaseOrderIndexModel):
    test_charfield = BaseField(models.CharField, max_length=100)
    test_fk = BaseField(
        models.ForeignKey,
        to=TestBaseModel,
        on_delete=models.CASCADE,
        unique_order_attribute=True,
    )
