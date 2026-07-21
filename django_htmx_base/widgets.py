# django
from django import forms


class WidgetStylerMixin:
    fields: dict[str, forms.Field]

    text_class = "form-control input-text"
    textarea_class = "form-control input-textarea"
    select_class = "form-select"
    checkbox_class = "form-check-input"
    radio_class = "form-check-input"

    text_attrs = {"autocomplete": "off"}
    textarea_attrs = {"rows": 3}
    select_attrs = {}
    checkbox_attrs = {}
    radio_attrs = {}

    def apply_widget_styles(self):
        """Applies classes and attrs to form fields."""
        widget_mapping = {
            forms.TextInput: (self.text_class, self.text_attrs),
            forms.EmailInput: (self.text_class, self.text_attrs),
            forms.Textarea: (self.textarea_class, self.textarea_attrs),
            forms.Select: (self.select_class, self.select_attrs),
            forms.CheckboxInput: (self.checkbox_class, self.checkbox_attrs),
            forms.RadioSelect: (self.radio_class, self.radio_attrs),
        }

        for field in self.fields.values():
            widget_type = type(field.widget)

            if widget_type in widget_mapping:
                css_class, default_attrs = widget_mapping[widget_type]

                if css_class:
                    existing_classes = field.widget.attrs.get("class", "")
                    field.widget.attrs["class"] = (
                        f"{existing_classes} {css_class}".strip()
                    )

                if default_attrs:
                    updated_attrs = {**default_attrs, **field.widget.attrs}
                    field.widget.attrs.update(updated_attrs)
