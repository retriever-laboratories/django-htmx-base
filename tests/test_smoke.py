import importlib.util

from django.test import TestCase

from tests.models import TestBaseModel

MODULES = ["admin", "models", "routers", "urls", "views", "viewsets"]


class HealthTestCase(TestCase):
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
        instance = TestBaseModel.objects.create(test_charfield="Hello")

        self.assertIsNotNone(instance.id)
        self.assertTrue(instance.is_active)
