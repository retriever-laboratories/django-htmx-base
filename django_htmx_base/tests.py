from django.test import TestCase


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
