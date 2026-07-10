from django.test import TestCase

from tests.models import TestBaseModel


class HtmxViewSetTestCase(TestCase):
    def test_the_list_action_shows_the_objects(self):
        TestBaseModel.objects.create(test_charfield="Hello")

        response = self.client.get("/test-base-models/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello")
