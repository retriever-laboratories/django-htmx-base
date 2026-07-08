from django.test import TestCase

from tests.models import Article


class HtmxViewSetTests(TestCase):
    def test_the_list_action_shows_the_objects(self):
        Article.objects.create(title="Hello")

        response = self.client.get("/articles/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello")
