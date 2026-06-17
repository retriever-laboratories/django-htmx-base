from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.query import QuerySet
from django.forms import Form
from django.forms import models as model_forms
from django.http import HttpResponseRedirect
from django.http import QueryDict
from django.views.generic import View
from django.views.generic.base import ContextMixin
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import MultipleObjectMixin


class GenericHtmxViewSet(TemplateResponseMixin, ModelFormMixin, MultipleObjectMixin, View):
    """
    Viewset in charge of consolidating common logic for handling list and object retrieval, context data preparation,
    template name resolution, and form processing for HTMX-based CRUD views.

    Specifically, it overwrites and extends the following methods from the generic class-based views:
    - get_queryset
    - get_context_data
    - get_context_object_name
    - get_template_names
    - get_form_class and get_form_kwargs

    """

    # Current action being handled, e.g. "list", "detail", "create", "edit", or "delete".
    action = None

    # Templates configuration.
    template_name_suffixes = {
        "list": "_list",
        "detail": "_detail",
        "create": "_form",
        "edit": "_form",
        "delete": "_confirm_delete",
    }

    # Context names configuration for list and object
    context_object_name = None
    context_object_list_name = None

    # Actions types separation for context data handling
    form_actions = {"create", "edit", "delete"}
    object_actions = {"detail", "edit", "delete"}
    list_actions = {"list"}

    def get_queryset(self):
        """
        Consolidated queryset retrieval for list and object actions.
        """
        if self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, QuerySet):
                queryset = queryset.all()
        elif self.model is not None:
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define %(cls)s.model, "
                "%(cls)s.queryset, or override %(cls)s.get_queryset()."
                % {"cls": self.__class__.__name__}
            )

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset

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
        if self.template_name is not None:
            return self._normalize_template_names(self.template_name)

        names = []
        
        if self.object is not None and self.template_name_field:
            name = getattr(self.object, self.template_name_field, None)
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

    def get_form_class(self):
        """
        Consolidated form class retrieval for create, edit, and delete actions.
        """
        form_class = self.form_class
        fields = self.fields

        if fields is not None and form_class:
            raise ImproperlyConfigured(
                "Specifying both 'fields' and 'form_class' is not permitted."
            )

        if form_class:
            return form_class

        if self.action == "delete":
            return Form

        if self.model is not None:
            model = self.model
        elif getattr(self, "object", None) is not None:
            model = self.object.__class__
        else:
            model = self.get_queryset().model

        if fields is None:
            raise ImproperlyConfigured(
                "Using %(cls)s without the 'fields' attribute is prohibited."
                % {"cls": self.__class__.__name__}
            )

        return model_forms.modelform_factory(model, fields=fields)

    def get_form_kwargs(self):
        """
        Add support for PATCH and handle data serialization for non-POST methods in form processing.
        """
        kwargs = {
            "initial": self.get_initial(),
            "prefix": self.get_prefix(),
        }

        if self.request.method in ("POST", "PUT", "PATCH"):
            kwargs.update(
                {
                    "data": self._get_request_data(),
                    "files": self.request.FILES,
                }
            )

        if hasattr(self, "object"):
            kwargs.update({"instance": self.object})

        return kwargs

    def _normalize_template_names(self, names):
        if names is None:
            return []
        if isinstance(names, str):
            return [names]
        return list(names)

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
    A viewset in charge of implementing the standard CRUD actions (list, detail, create, edit, delete)
    with HTMX support and flexible configuration for templates, forms, and context data.
    It also is able to route HTTP methods and URL patterns to the appropriate action methods.
    """
    action_routes = {
        "get": {
            "list": "list",
            "detail": "detail",
            "create": "create_form",
            "edit": "edit_form",
            "delete": "delete_form",
        },
        "post": {
            "create": "create",
            "edit": "edit",
            "delete": "destroy",
        },
        "put": {
            "edit": "edit",
        },
        "patch": {
            "edit": "edit",
        },
        "delete": {
            "delete": "destroy",
        },
    }

    def get(self, request, *args, **kwargs):
        return self.route_action(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.route_action(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.route_action(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.route_action(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.route_action(request, *args, **kwargs)

    def route_action(self, request, *args, **kwargs):
        method = request.method.lower()
        url_name = request.resolver_match.url_name
        action_name = self.action_routes.get(method, {}).get(url_name)

        if action_name is None:
            return self.http_method_not_allowed(request, *args, **kwargs)

        action = getattr(self, action_name)
        return action(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        self.action = "list"
        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list)
        return self.render_to_response(context)

    def detail(self, request, *args, **kwargs):
        self.action = "detail"
        self.object = self.get_object()
        context = self.get_context_data(obj=self.object)
        return self.render_to_response(context)

    def create_form(self, request, *args, **kwargs):
        self.action = "create"
        self.object = None
        return self.render_form(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self.action = "create"
        self.object = None
        return self.process_form(request, *args, **kwargs)

    def edit_form(self, request, *args, **kwargs):
        self.action = "edit"
        self.object = self.get_object()
        return self.render_form(request, *args, **kwargs)

    def edit(self, request, *args, **kwargs):
        self.action = "edit"
        self.object = self.get_object()
        return self.process_form(request, *args, **kwargs)

    def delete_form(self, request, *args, **kwargs):
        self.action = "delete"
        self.object = self.get_object()
        return self.render_form(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self.action = "destroy"
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def render_form(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def process_form(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)
