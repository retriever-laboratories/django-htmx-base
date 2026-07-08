from django.db import models

from django_htmx_base.models import BaseField
from django_htmx_base.models import BaseModel


class Article(BaseModel):
    title = BaseField(models.CharField, max_length=100)
