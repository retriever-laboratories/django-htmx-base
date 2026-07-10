from django.test import TestCase

from tests.models import TestBaseModel


class HtmxViewSetTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.instance = TestBaseModel.objects.create(test_charfield="Hello")

    def test_the_list_action_shows_the_objects(self):
        response = self.client.get("/test-base-models/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello")
