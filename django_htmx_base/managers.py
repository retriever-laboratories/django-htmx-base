from django.db import models


class ActiveQuerySet(models.QuerySet):
    """
    Custom QuerySet to allow chained filtering.
    """

    def active(self):
        return self.filter(is_active=True)


class ActiveManager(models.Manager):
    """
    Custom Manager that overrides the default behavior of all().
    """

    def get_queryset(self):
        return ActiveQuerySet(self.model, using=self._db).active()

    def all_objects(self):
        return super().get_queryset()


class DefaultManager(models.Manager):
    pass
