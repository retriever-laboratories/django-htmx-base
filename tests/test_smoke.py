from django.test import TestCase

from tests.models import Article


class LibraryHealthTests(TestCase):
    def test_every_module_of_the_library_imports(self):
        from django_htmx_base import admin  # noqa: F401
        from django_htmx_base import models  # noqa: F401
        from django_htmx_base import routers  # noqa: F401
        from django_htmx_base import urls  # noqa: F401
        from django_htmx_base import views  # noqa: F401
        from django_htmx_base import viewsets  # noqa: F401

    def test_the_library_can_be_used(self):
        article = Article.objects.create(title="Hello")

        self.assertIsNotNone(article.id)
        self.assertTrue(article.is_active)
