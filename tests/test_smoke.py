import importlib.util

from django.test import TestCase

from tests.models import TestBaseModel

MODULES = ["admin", "models", "routers", "urls", "views", "viewsets"]


class HealthTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.instance = TestBaseModel.objects.create(test_charfield="Hello")

    def test_modules_exists(self):
        for name in MODULES:
            module = f"django_htmx_base.{name}"
            module_exists = bool(importlib.util.find_spec(module))
            self.assertEqual(
                module_exists,
                True,
                f"The module '{module}' does not exist.",
            )

    def test_base_model_inheritance(self):
        self.assertIsNotNone(self.instance.id)
        self.assertTrue(self.instance.is_active)
