from django.db import models

from django_htmx_base.models import BaseField
from django_htmx_base.models import BaseModel


class TestBaseModel(BaseModel):
    test_charfield = BaseField(models.CharField, max_length=100)
    test_display_field = BaseField(
        models.CharField, max_length=100, null=True, blank=True
    )
