# django
from django.forms import HiddenInput


class DisplayOnlyWidget(HiddenInput):
    def __init__(self, attrs=None):
        if attrs is not None:
            attrs = attrs.copy()
        else:
            attrs = {}

        attrs["data-display-only"] = True

        super().__init__(attrs)

    @property
    def is_display_only(self):
        return "data-display-only" in self.attrs
