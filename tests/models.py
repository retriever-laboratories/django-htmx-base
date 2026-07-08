# django
from django.db import models

# models
from django_htmx_base.models import BaseField
from django_htmx_base.models import BaseModel


class Article(BaseModel):
    """A minimal model using the library, like a real project would."""

    title = BaseField(models.CharField, max_length=100)
