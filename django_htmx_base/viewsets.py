# standard
import inspect
from enum import StrEnum
from functools import update_wrapper

# django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.db import models
from django.forms import Form
from django.forms import models as model_forms
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import QueryDict
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import View
from django.views.generic.base import ContextMixin
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import MultipleObjectMixin

# models
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
    - get_model_name
    - get_template_names
    - get_form_class and get_form_kwargs

    """

    allow_empty = True
    content_type = None
    fields = None
    form_class = None
    initial = {}
    model = None
    object = None
    ordering = None
    page_kwarg = "page"
    paginate_by = None
    paginate_orphans = 0
    paginator_class = Paginator
    pk_url_kwarg = "pk"
    prefix = None
    query_pk_and_slug = False
    queryset = None
    response_class = TemplateResponse
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_url = None
    template_engine = None

    # Templates configuration.
    detail_template_name = None
    form_template_name = None
    list_template_name = None
    suffix_join = "-"
    use_app_templates = False
    use_model_templates = True

    # Context names configuration for list and object
    model_name = None
    context_object_list_name = None

    # Actions types separation for context data handling
    list_actions = {HtmxAction.LIST}
    object_actions = {HtmxAction.DETAIL, HtmxAction.EDIT, HtmxAction.DELETE}
    form_actions = object_actions | {HtmxAction.CREATE}

    # Pagination config
    page_size_options = (10, 50, 100)
    paginate_by = settings.PAGINATE_BY if hasattr(settings, "PAGINATE_BY") else None

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_queryset(queryset, self._get_model())

    def get_model_name(self, queryset=None, obj=None):
        """
        Consolidated context object name retrieval for both list and object actions.
        """
        if obj is not None:
            if self.model_name:
                return self.model_name
            if isinstance(obj, models.Model):
                return obj._meta.model_name

        if queryset is not None:
            if self.context_object_list_name:
                return self.context_object_list_name
            if hasattr(queryset, "model"):
                return "%s_list" % queryset.model._meta.model_name

        return None

    def get_context_data(self, queryset=None, obj=None, **kwargs):
        """
        Consolidated context data preparation for the different action types
        """
        context = {}

        if self.action in self.list_actions:
            object_list = queryset if queryset is not None else self.get_queryset()
            if object_list is not None:
                context.update(self.get_list_context_data(object_list))

        if self.action in self.object_actions:
            if not obj:
                obj = self.object or self.get_object()

            if obj and obj is not None:
                context.update(self.get_object_context_data(obj))

        if self.action in self.form_actions and "form" not in kwargs:
            context.update({"form": self.get_form()})

        context.update(kwargs)
        return ContextMixin.get_context_data(self, **context)

    def get_list_context_data(self, queryset=None):
        """
        Set context variables for list actions, including pagination if applicable.
        """
        if queryset is None:
            queryset = self.queryset

        page_size = self.get_paginate_by()
        model_name = self.get_model_name(queryset=queryset)

        if page_size:
            paginator, page, queryset, is_paginated = self.paginate_queryset(
                queryset,
                page_size,
            )
            context = {
                "paginator": paginator,
                "page_obj": page,
                "is_paginated": is_paginated,
                "object_list": queryset,
            }
        else:
            context = {
                "paginator": None,
                "page_obj": None,
                "is_paginated": False,
                "object_list": queryset,
            }

        context["model"] = self._get_model()

        if model_name is not None:
            context[model_name] = queryset

        return context

    def get_object_context_data(self, obj):
        """Set context variables for single object actions."""
        context = {"object": obj}
        model_name = self.get_model_name(obj=obj)
        if model_name:
            context[model_name] = obj
            context["model"] = self._get_model()
        return context

    def get_template_names(self):
        """
        Consolidated template name retrieval that checks explicit templates,
        object-specific template fields, and app or model-based defaults.
        """
        template_name = self._get_action_template_name()
        if template_name is not None:
            return [template_name]

        suffix = self._get_action_template_name(default=True)
        if self.use_model_templates or self.use_app_templates:
            model = self._get_model()
            names = []
            if not model:
                raise ImproperlyConfigured(
                    "Cannot determine model for template name resolution. "
                    "Disable use_model_templates and use_app_templates "
                    "in the viewset."
                )

            app_label = model._meta.app_label
            model_name = model._meta.model_name

            if self.use_model_templates:
                names.append(f"{app_label}/{model_name}/{suffix}.html")
                names.append(f"{app_label}/{model_name}{self.suffix_join}{suffix}.html")

            elif self.use_app_templates:
                names.append(f"{app_label}/{suffix}.html")

            return names

        return [f"{suffix}.html"]

    def _get_action_template_name(self, default=False):
        if self.action in self.list_actions:
            return HtmxAction.LIST if default else self.list_template_name

        if self.action in {HtmxAction.CREATE, HtmxAction.EDIT}:
            return HtmxAction.FORM if default else self.form_template_name

        if self.action == HtmxAction.DETAIL:
            return HtmxAction.DETAIL if default else self.detail_template_name

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

    def is_htmx(self):
        return self.request.headers.get("HX-Request") == "true"

    def get_paginate_by(self):
        self.paginate_by = self.request.GET.get("page_size", self.paginate_by)
        return self.paginate_by

    def filter_queryset(self, queryset, model):
        filtrable_fields = self._get_filtrable_fields(model)
        if not filtrable_fields:
            return queryset

        filters = {}
        restricted_params = {"o", "page", "page_size"}

        filters_params = [
            param
            for param in self.request.GET.lists()
            if param[0] not in restricted_params and param[0] in filtrable_fields
        ]

        for filter_param, values in filters_params:
            values = [value for value in values if value]
            if not values:
                continue

            filter_input_type = filtrable_fields[filter_param]
            if filter_input_type == FilterInputType.TEXT:
                filters[f"{filter_param}__icontains"] = values[-1]
            elif len(values) == 1:
                filters[filter_param] = values[0]
            else:
                filters[f"{filter_param}__in"] = values

        if filters:
            return queryset.filter(**filters)

        return queryset

    def get_success_url(self):
        try:
            return super().get_success_url()
        except ImproperlyConfigured:
            if self.action in self.list_actions or self.action == HtmxAction.DELETE:
                route_action = HtmxAction.LIST
                kwargs = None
            elif self.action in self.object_actions or self.action == HtmxAction.CREATE:
                route_action = HtmxAction.DETAIL
                kwargs = {self.pk_url_kwarg: self.object.pk}
            else:
                raise ImproperlyConfigured(
                    f"No success URL is available for the {self.action!r} action."
                )

            route_name = f"{self.basename}-{route_action}"
            namespace = self.request.resolver_match.namespace
            if namespace:
                route_name = f"{namespace}:{route_name}"

            return reverse(route_name, kwargs=kwargs)

    def _get_ordering_params(self, model):
        sortable_fields = self._get_sortable_fields(model)
        if not sortable_fields:
            return ()

        ordering_list = self.request.GET.getlist("o")
        ordering = [x for x in ordering_list if x]
        return [x for x in ordering if x.lstrip("-") in sortable_fields]

    def _get_sortable_fields(self, model):
        if model is None or not hasattr(model, "sortable_fields"):
            return set()

        return set(model.sortable_fields())

    def _get_filtrable_fields(self, model):
        if model is None or not hasattr(model, "get_filtrable_fields"):
            return {}

        return {
            field.name: field.filter_input_type
            for field in model.get_filtrable_fields()
        }

    def _get_model(self):
        obj = getattr(self, "object", None)
        if obj is not None and hasattr(obj, "_meta"):
            return obj.__class__

        if self.model is not None:
            return self.model

        queryset = getattr(self, "queryset", None)
        if queryset is not None and hasattr(queryset, "model"):
            return queryset.model

        return None

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
        self.model = self._get_model()
        if hasattr(self, "action_map"):
            handler_action = self.action_map.get(request.method.lower())
            self.action = getattr(self, "route_action", handler_action)

        self._register_custom_action(handler_action)

        if self.action in self.list_actions:
            self.ordering = self._get_ordering_params(self.model)

        if self.action in self.object_actions:
            self.object = self.get_object()

        self.context = self.get_context_data(obj=self.object, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def _register_custom_action(self, handler_action):
        handler = getattr(self, handler_action, None)
        if not getattr(handler, "is_custom_action", False):
            return

        self.object_actions = set(self.object_actions)
        self.list_actions = set(self.list_actions)

        if self.route_detail:
            self.object_actions.add(self.action)
        else:
            self.list_actions.add(self.action)

    def list(self, request, *args, **kwargs):  # noqa: ARG002
        return self.render_to_response(self.context)

    def detail(self, request, *args, **kwargs):  # noqa: ARG002
        return self.render_to_response(self.context)

    def create(self, request, *args, **kwargs):  # noqa: ARG002
        if request.method == "GET":
            return self.render_to_response(self.context)
        elif request.method == "POST":
            return self.process_form()

    def edit(self, request, *args, **kwargs):  # noqa: ARG002
        return self.process_form()

    def destroy(self, request, *args, **kwargs):  # noqa: ARG002
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def process_form(self):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    @action(methods=["get"], detail=False)
    def download(self, request):  # noqa: ARG002

        queryset = self.get_queryset()
        model = self._get_model()

        if not hasattr(model, "is_downloadable") or not model.is_downloadable():
            return HttpResponse(content="Downloading not allowed.", status=403)

        csv_content = model.to_csv(queryset)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{model.__name__}.csv"'
        return response
