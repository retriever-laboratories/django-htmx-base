from django.db import models

from django_htmx_base.models import BaseField
from django_htmx_base.models import BaseModel
from django_htmx_base.models import BaseModelUserTracked


class TestBaseModel(BaseModel):
    test_charfield = BaseField(models.CharField, max_length=100)


class TestBaseModelUserTracked(BaseModelUserTracked):
    test_charfield = BaseField(models.CharField, max_length=100)
