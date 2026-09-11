# standard
import importlib.util

# django
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import override_settings
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
        formset = self.get_formset(url)
        initial_management_data = formset.management_form.initial
        prefix = formset.management_form.prefix
        prefixed_management_data = {
            f"{prefix}-{key}": value for key, value in initial_management_data.items()
        }

        if total_forms is not None:
            prefixed_management_data[f"{prefix}-TOTAL_FORMS"] = str(total_forms)

        return prefixed_management_data

    def get_view_instance(self, url):
        response = self.client.get(url)
        return response.context["view"]

    def get_formset(self, url):
        view_instance = self.get_view_instance(url)
        return view_instance.get_formset()

    def get_initial_payload(self, url, total_forms=1):
        formset = self.get_formset(url)
        payload = self.get_formset_management_data(url, total_forms)

        for i, form in enumerate(formset.forms):
            for field_name in form.fields:
                field_value = form.get_initial_for_field(
                    form.fields[field_name], field_name
                )

                if hasattr(field_value, "pk"):
                    field_value = field_value.pk
                elif field_value is None:
                    field_value = ""

                payload[f"{formset.prefix}-{i}-{field_name}"] = field_value

        return payload


class AppTestCase(FormsetTestHelper, TestCase):
    instance = None

    @classmethod
    def setUpTestData(cls):
        cls.instance = TestBaseModel.objects.create(
            test_charfield="Hello", test_display_field="This is not editable"
        )

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
        initial_obj_count = TestBaseModel.objects.count()
        url = reverse("testbasemodel-create")
        payload = self.get_initial_payload(url)

        response = self.client.post(url, data=payload)

        self.assertEqual(TestBaseModel.objects.count(), initial_obj_count)
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

    def test_custom_form_create(self):
        url = reverse("testform-create")
        view_instance = self.get_view_instance(url)
        form_class = view_instance.form_class
        self.assertNotIn("is_active", form_class._meta.fields)

    def test_form_display_only_fields(self):
        url = reverse("testform-edit", kwargs={"pk": self.instance.pk})
        response = self.client.get(url)

        self.assertIn(
            '<span class="plain-text-value">This is not editable</span>',
            response.text,
        )
        self.assertIn('type="hidden"', response.text)
        self.assertIn("data-display-only", response.text)

    def test_custom_formset(self):
        url = reverse("testformset-edit", kwargs={"pk": self.instance.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        payload = self.get_initial_payload(url)
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 302)


class UserTrackedModelTestCase(FormsetTestHelper, TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username="test-user",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_user_tracked_formset_post(self):
        url = reverse("testbasemodel-create")
        post_payload = self.get_initial_payload(url)
        post_payload.update(
            {
                "form-0-test_charfield": "User tracked string",
            }
        )

        response = self.client.post(url, data=post_payload)

        new_instance = TestBaseModel.objects.latest("created_at")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(new_instance.created_by, self.user)
        self.assertEqual(new_instance.updated_by, self.user)

    def test_user_tracked_formset_post_ignores_anonymous_user(self):
        self.client.logout()
        url = reverse("testbasemodel-create")
        management_data = self.get_formset_management_data(url)
        post_payload = {
            **management_data,
            "form-0-test_charfield": "Anonymous user string",
        }

        response = self.client.post(url, data=post_payload)

        new_instance = TestBaseModel.objects.latest("created_at")
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(new_instance.created_by)
        self.assertIsNone(new_instance.updated_by)

    def test_user_tracked_formset_edit_only_updates_updated_by(self):
        original_user = get_user_model().objects.create(
            username="original-user",
            password="test-password",
        )
        instance = TestBaseModel.objects.create(
            test_charfield="Original string",
            created_by=original_user,
            updated_by=original_user,
        )
        url = reverse("testbasemodel-edit", kwargs={"pk": instance.pk})
        post_payload = self.get_initial_payload(url)
        post_payload.update(
            {
                "form-0-test_charfield": "Updated string",
            }
        )

        response = self.client.post(url, data=post_payload)

        instance.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(instance.test_charfield, "Updated string")
        self.assertEqual(instance.created_by, original_user)
        self.assertEqual(instance.updated_by, self.user)


class SoftDeleteTestCase(TestCase):
    obj = None

    @classmethod
    def setUpTestData(cls):
        cls.obj = TestBaseModel.objects.create(test_charfield="Hello")

    @override_settings(SOFT_DELETE=True)
    def test_delete_keeps_the_row(self):
        self.obj.delete()

        self.assertFalse(TestBaseModel.objects.get(pk=self.obj.pk).is_active)

    @override_settings(SOFT_DELETE=False)
    def test_delete_removes_the_row(self):
        self.obj.delete()

        self.assertFalse(TestBaseModel.objects.filter(pk=self.obj.pk).exists())

    @override_settings(SOFT_DELETE=True)
    def test_restore_reactivates_the_row(self):
        self.obj.delete()
        self.obj.restore()

        self.assertTrue(TestBaseModel.objects.get(pk=self.obj.pk).is_active)
