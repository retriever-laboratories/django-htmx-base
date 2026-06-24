import inspect
from enum import StrEnum
from functools import update_wrapper

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.forms import Form
from django.forms import models as model_forms
from django.http import HttpResponseRedirect
from django.http import QueryDict
from django.views.generic import View
from django.views.generic.base import ContextMixin
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import MultipleObjectMixin

from django_htmx_base.models import FilterInputType


def action(methods=None, detail=None, url_path=None, url_name=None):
    if detail is None:
        raise TypeError("The detail argument must be provided.")

    if not isinstance(detail, bool):
        raise TypeError("The detail argument must be True or False.")

    if methods is None:
        methods = ["get"]
    elif isinstance(methods, str):
        methods = [methods]

    if not methods:
        raise TypeError("The methods argument must not be empty.")

    methods = [method.lower() for method in methods]

    def decorator(func):
        func.mapping = {method: func.__name__ for method in methods}
        func.detail = detail
        func.url_path = url_path or func.__name__
        func.url_name = url_name or func.__name__
        func.is_custom_action = True
        return func

    return decorator


class HtmxAction(StrEnum):
    LIST = "list"
    DETAIL = "detail"
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    DESTROY = "destroy"
    FORM = "form"


class GenericHtmxViewSet(
    TemplateResponseMixin, MultipleObjectMixin, ModelFormMixin, View
):
    """
    Viewset in charge of consolidating common logic
    for handling list and object retrieval, context data preparation,
    template name resolution, and form processing for HTMX-based CRUD views.

    Specifically, it overwrites and extends the following methods
    from the generic class-based views:
    - get_context_data
    - get_context_object_name
    - get_template_names
    - get_form_class and get_form_kwargs

    """

    # Current action being handled
    action = None

    # Templates configuration.
    list_template_name = None
    detail_template_name = None
    form_template_name = None

    template_name_suffixes = {
        HtmxAction.LIST: "_list",
        HtmxAction.DETAIL: "_detail",
        HtmxAction.CREATE: "_form",
        HtmxAction.EDIT: "_form",
        HtmxAction.DELETE: "_confirm_delete",
    }

    # Context names configuration for list and object
    context_object_name = None
    context_object_list_name = None

    # Actions types separation for context data handling
    form_actions = {HtmxAction.CREATE, HtmxAction.EDIT, HtmxAction.DELETE}
    object_actions = {HtmxAction.DETAIL, HtmxAction.EDIT, HtmxAction.DELETE}
    list_actions = {HtmxAction.LIST}
    page_size_options = (10, 50, 100)

    def get_context_object_name(self, object_list=None, obj=None):
        """
        Consolidated context object name retrieval for both list and object actions.
        """
        if obj is not None:
            if self.context_object_name:
                return self.context_object_name
            if isinstance(obj, models.Model):
                return obj._meta.model_name

        if object_list is not None:
            if self.context_object_list_name:
                return self.context_object_list_name
            if hasattr(object_list, "model"):
                return "%s_list" % object_list.model._meta.model_name

        return None

    def get_context_data(self, object_list=None, obj=None, **kwargs):
        """
        Consolidated context data preparation for the different action types
        """
        context = {}

        if self.action in self.list_actions:
            object_list = object_list if object_list is not None else self.object_list
            if object_list is not None:
                context.update(self.get_list_context_data(object_list))

        if self.action in self.object_actions:
            obj = obj if obj is not None else self.object
            if obj is not None:
                context.update(self.get_object_context_data(obj))

        if self.action in self.form_actions and "form" not in kwargs:
            kwargs["form"] = self.get_form()

        context.update(kwargs)
        return ContextMixin.get_context_data(self, **context)

    def get_list_context_data(self, object_list):
        """
        Set context variables for list actions, including pagination if applicable.
        """
        page_size = self.get_paginate_by(object_list)
        context_object_name = self.get_context_object_name(object_list=object_list)

        if page_size:
            paginator, page, object_list, is_paginated = self.paginate_queryset(
                object_list,
                page_size,
            )
            context = {
                "paginator": paginator,
                "page_obj": page,
                "is_paginated": is_paginated,
                "object_list": object_list,
            }
        else:
            context = {
                "paginator": None,
                "page_obj": None,
                "is_paginated": False,
                "object_list": object_list,
            }

        if context_object_name is not None:
            context[context_object_name] = object_list
        context.update(self.get_list_metadata_context())
        return context

    def get_object_context_data(self, obj):
        """Set context variables for single object actions."""
        context = {"object": obj}
        context_object_name = self.get_context_object_name(obj=obj)
        if context_object_name:
            context[context_object_name] = obj
        return context

    def get_template_names(self):
        """
        Consolidated template name retrieval that checks explicit templates,
        object-specific template fields, and model-based defaults.
        """
        template_name = self._get_action_template_name()
        if template_name is not None:
            return self._normalize_template_names(template_name)

        names = []

        template_name_field = getattr(self, "template_name_field", None)
        if self.object is not None and template_name_field:
            name = getattr(self.object, template_name_field, None)
            if name:
                names.insert(0, name)

        model = self._get_template_model()
        if model is not None:
            opts = model._meta
            names.append(
                "%s/%s%s.html"
                % (opts.app_label, opts.model_name, self._get_template_name_suffix())
            )

        if not names:
            raise ImproperlyConfigured(
                "%(cls)s requires template names. Define %(cls)s.template_name, "
                "%(cls)s.model, or override %(cls)s.get_template_names()."
                % {"cls": self.__class__.__name__}
            )

        return names

    def _get_action_template_name(self):
        if self.action in self.list_actions:
            return self.list_template_name

        if self.action in {HtmxAction.CREATE, HtmxAction.EDIT}:
            return self.form_template_name

        if self.action == HtmxAction.DETAIL:
            return self.detail_template_name

        return self.template_name

    def get_form_class(self):
        """
        Consolidated form class retrieval for create, edit, and delete actions.
        """
        if self.action == HtmxAction.DELETE:
            return Form

        return super().get_form_class()

    def get_form_kwargs(self):
        """
        Add support for PATCH and handle data serialization
        for non-POST methods in form processing.
        """
        kwargs = super().get_form_kwargs()

        if self.request.method in ("PUT", "PATCH"):
            kwargs.update(
                {
                    "data": self._get_request_data(),
                    "files": self.request.FILES,
                }
            )

        if not issubclass(self.get_form_class(), model_forms.ModelForm):
            kwargs.pop("instance", None)

        return kwargs

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get("page_size")
        if page_size is None:
            return super().get_paginate_by(queryset)

        try:
            page_size = int(page_size)
        except ValueError:
            return super().get_paginate_by(queryset)

        if page_size < 1:
            return super().get_paginate_by(queryset)

        return page_size

    def get_list_metadata_context(self):
        model = self._get_template_model()
        context = {
            "model": model,
            "page_size_options": list(self.page_size_options),
        }

        if model is not None and hasattr(model, "table_columns"):
            context["table"] = {"columns": model.table_columns()}

        if model is not None and hasattr(model, "filtrable_fields"):
            context["filters"] = model.filtrable_fields()

        return context

    def set_ordering(self, model):
        ordering_params = self._get_ordering_params(model)
        if not ordering_params:
            return

        default_ordering = self._normalize_ordering(self.get_ordering())
        self.ordering = self._dedupe_ordering(ordering_params + default_ordering)

    def filter_queryset(self, queryset, model):
        filtrable_fields = self._get_filtrable_fields(model)
        if not filtrable_fields:
            return queryset

        filters = {}

        for name, values in self.request.GET.lists():
            if name in {"o", "page", "page_size"} or name not in filtrable_fields:
                continue

            values = [value for value in values if value != ""]
            if not values:
                continue

            filter_input_type = filtrable_fields[name]
            if filter_input_type == FilterInputType.TEXT:
                filters[f"{name}__icontains"] = values[-1]
            elif len(values) == 1:
                filters[name] = values[0]
            else:
                filters[f"{name}__in"] = values

        if filters:
            return queryset.filter(**filters)

        return queryset

    def _normalize_template_names(self, names):
        if names is None:
            return []
        if isinstance(names, str):
            return [names]
        return list(names)

    def _normalize_ordering(self, ordering):
        if not ordering:
            return ()
        if isinstance(ordering, str):
            return (ordering,)
        return tuple(ordering)

    def _dedupe_ordering(self, ordering):
        result = []
        seen = set()

        for value in ordering:
            field_name = value.removeprefix("-")
            if field_name in seen:
                continue
            seen.add(field_name)
            result.append(value)

        return tuple(result)

    def _get_ordering_params(self, model):
        sortable_fields = self._get_sortable_fields(model)
        if not sortable_fields:
            return ()

        ordering = []

        for value in self.request.GET.getlist("o"):
            if not value:
                continue

            value = value.strip()
            field_name = value.removeprefix("-")
            if field_name in sortable_fields:
                ordering.append(value)

        return tuple(ordering)

    def _get_sortable_fields(self, model):
        if model is None or not hasattr(model, "sortable_fields"):
            return set()

        return set(model.sortable_fields())

    def _get_filtrable_fields(self, model):
        if model is None or not hasattr(model, "filtrable_fields"):
            return {}

        return {
            filter_config["field"]: FilterInputType(filter_config["filter_input_type"])
            for filter_config in model.filtrable_fields()
        }

    def _get_template_model(self):
        obj = getattr(self, "object", None)
        if obj is not None and hasattr(obj, "_meta"):
            return obj.__class__

        object_list = getattr(self, "object_list", None)
        if object_list is not None and hasattr(object_list, "model"):
            return object_list.model

        if self.model is not None:
            return self.model

        queryset = getattr(self, "queryset", None)
        if queryset is not None and hasattr(queryset, "model"):
            return queryset.model

        return None

    def _get_template_name_suffix(self):
        if not self.template_name_suffixes:
            return ""
        return self.template_name_suffixes.get(self.action, "")

    def _get_request_data(self):
        if self.request.method == "POST":
            return self.request.POST

        content_type = self.request.content_type or ""
        if content_type.startswith("application/x-www-form-urlencoded"):
            return QueryDict(self.request.body, encoding=self.request.encoding)

        return QueryDict(encoding=self.request.encoding)


class HtmxViewSet(GenericHtmxViewSet):
    """
    A viewset in charge of implementing the standard CRUD actions
    with HTMX support and flexible configuration for templates, forms, and context data.
    The router maps HTTP methods to these action methods when building URL patterns.
    """

    @classmethod
    def get_extra_actions(cls):
        return [
            method
            for _, method in inspect.getmembers(cls, predicate=callable)
            if getattr(method, "is_custom_action", False)
        ]

    @classmethod
    def as_view(cls, actions=None, **initkwargs):
        if actions is None:
            raise TypeError(
                "The actions argument must be provided when calling "
                ".as_view() on a HtmxViewSet."
            )

        if not actions:
            raise TypeError("The actions argument must not be empty.")

        for method in actions:
            if method.lower() not in cls.http_method_names:
                raise TypeError(
                    "%s() received an invalid HTTP method %r." % (cls.__name__, method)
                )

        actions = {method.lower(): action for method, action in actions.items()}

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            self.action_map = actions

            for method, action in actions.items():
                handler = getattr(self, action)
                setattr(self, method, handler)

            self.setup(request, *args, **kwargs)
            if not hasattr(self, "request"):
                raise AttributeError(
                    "%s instance has no 'request' attribute. Did you override "
                    "setup() and forget to call super()?" % cls.__name__
                )
            return self.dispatch(request, *args, **kwargs)

        view.view_class = cls
        view.view_initkwargs = initkwargs
        view.actions = actions

        update_wrapper(view, cls, updated=())
        update_wrapper(view, cls.dispatch, assigned=())
        return view

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self, "action_map"):
            self.action = self.action_map.get(request.method.lower())
        return super().dispatch(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):  # noqa: ARG002
        self.action = HtmxAction.LIST
        model = self._get_template_model()
        self.set_ordering(model)
        self.object_list = self.filter_queryset(self.get_queryset(), model)
        context = self.get_context_data(object_list=self.object_list)
        return self.render_to_response(context)

    def detail(self, request, *args, **kwargs):  # noqa: ARG002
        self.action = HtmxAction.DETAIL
        self.object = self.get_object()
        context = self.get_context_data(obj=self.object)
        return self.render_to_response(context)

    def create(self, request, *args, **kwargs):  # noqa: ARG002
        self.action = HtmxAction.CREATE
        self.object = None
        return self.process_form(request, *args, **kwargs)

    def edit(self, request, *args, **kwargs):  # noqa: ARG002
        self.action = HtmxAction.EDIT
        self.object = self.get_object()
        return self.process_form(request, *args, **kwargs)

    def form(self, request, *args, **kwargs):  # noqa: ARG002
        self.action = getattr(self, "route_action", self.action)
        if self.action in self.object_actions:
            self.object = self.get_object()
        else:
            self.object = None
        return self.render_form(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):  # noqa: ARG002
        self.action = HtmxAction.DESTROY
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def render_form(self, request, *args, **kwargs):  # noqa: ARG002
        return self.render_to_response(self.get_context_data())

    def process_form(self, request, *args, **kwargs):  # noqa: ARG002
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)
