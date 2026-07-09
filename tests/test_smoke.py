from django.test import TestCase

from tests.models import Article


class LibraryHealthTests(TestCase):
    def test_the_library_can_be_used(self):
        article = Article.objects.create(title="Hello")

        self.assertIsNotNone(article.id)
        self.assertTrue(article.is_active)
