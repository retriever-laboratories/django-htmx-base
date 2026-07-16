# standard
import importlib.util

# django
from django.test import TestCase
from django.urls import reverse

# models
from tests.models import TestBaseModel

MODULES = ["admin", "models", "routers", "urls", "views", "viewsets"]


class FormsetTestHelper(TestCase):
    def get_formset_management_data(self, url, total_forms=1):
        """
        Performs a dynamic GET request to fetch the root view
        formset configuration.
        """
        response = self.client.get(url)
        view_instance = response.context["view"]
        formset = view_instance.get_formset()
        initial_management_data = formset.management_form.initial
        prefixed_management_data = {
            f"form-{key}": value for key, value in initial_management_data.items()
        }
        prefixed_management_data["form-TOTAL_FORMS"] = str(total_forms)

        return prefixed_management_data


class AppTestCase(FormsetTestHelper, TestCase):
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

    def test_list_action(self):
        url = reverse("testbasemodel-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello")

    def test_empty_formsets_post(self):
        url = reverse("testbasemodel-create")
        management_data = self.get_formset_management_data(url)
        post_payload = {
            **management_data,
        }

        response = self.client.post(url, data=post_payload)
        formset = response.context["view"].formset

        self.assertFalse(formset.is_valid())
        self.assertEqual(response.status_code, 200)

    def test_single_formsets_post(self):
        url = reverse("testbasemodel-create")
        management_data = self.get_formset_management_data(url)
        initial_obj_count = TestBaseModel.objects.count()
        test_string = "I am testing using this string"
        post_payload = {
            **management_data,
            "form-0-test_charfield": test_string,
        }

        response = self.client.post(url, data=post_payload)

        new_instance = TestBaseModel.objects.latest("created_at")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TestBaseModel.objects.count(), initial_obj_count + 1)
        self.assertEqual(new_instance.test_charfield, test_string)

    def test_multiple_formset_posts(self):
        url = reverse("testbasemodel-create")
        initial_obj_count = TestBaseModel.objects.count()
        management_data = self.get_formset_management_data(url, 2)
        post_payload = {
            **management_data,
            "form-0-test_charfield": "First String",
            "form-1-test_charfield": "Second String",
        }

        response = self.client.post(url, data=post_payload)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(TestBaseModel.objects.count(), initial_obj_count + 2)

    def test_download_extra_action(self):
        url = reverse("testbasemodel-download")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Content-Type"],
            "text/csv",
        )
        self.assertEqual(
            response.headers["Content-Disposition"],
            f"attachment; filename='{self.instance._meta.model.__name__}.csv'",
        )
