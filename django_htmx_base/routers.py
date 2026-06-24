from django.core.exceptions import ImproperlyConfigured
from django.urls import path

from django_htmx_base.viewsets import HtmxAction


class Route:
    def __init__(self, url, mapping, name, detail):
        self.url = url
        self.mapping = mapping
        self.name = name
        self.detail = detail


class HtmxRouter:
    """
    Generate CRUD URL patterns for HtmxViewSet classes.
    """

    routes = [
        Route(
            url="",
            mapping={"get": HtmxAction.LIST},
            name=HtmxAction.LIST,
            detail=False,
        ),
        Route(
            url=HtmxAction.CREATE,
            mapping={"get": HtmxAction.FORM, "post": HtmxAction.CREATE},
            name=HtmxAction.CREATE,
            detail=False,
        ),
        Route(
            url="{pk}",
            mapping={"get": HtmxAction.DETAIL},
            name=HtmxAction.DETAIL,
            detail=True,
        ),
        Route(
            url=f"{{pk}}/{HtmxAction.EDIT}",
            mapping={
                "get": HtmxAction.FORM,
                "post": HtmxAction.EDIT,
                "put": HtmxAction.EDIT,
                "patch": HtmxAction.EDIT,
            },
            name=HtmxAction.EDIT,
            detail=True,
        ),
        Route(
            url=f"{{pk}}/{HtmxAction.DELETE}",
            mapping={
                "get": HtmxAction.FORM,
                "post": HtmxAction.DESTROY,
                "delete": HtmxAction.DESTROY,
            },
            name=HtmxAction.DELETE,
            detail=True,
        ),
    ]

    def __init__(self):
        self.registry = []

    def register(self, prefix, viewset, basename=None):
        if basename is None:
            basename = self.get_default_basename(viewset)

        self.registry.append((prefix.strip("/"), viewset, basename))

    def get_default_basename(self, viewset):
        model = getattr(viewset, "model", None)
        if model is not None:
            return model._meta.model_name

        queryset = getattr(viewset, "queryset", None)
        if queryset is not None and hasattr(queryset, "model"):
            return queryset.model._meta.model_name

        raise ImproperlyConfigured(
            "%(cls)s is missing a basename. Pass basename=... to register(), "
            "or define %(cls)s.model or %(cls)s.queryset." % {"cls": viewset.__name__}
        )

    @property
    def urls(self):
        urls = []

        for prefix, viewset, basename in self.registry:
            pk = self.get_pk_path(viewset)

            for route in self.get_routes(viewset):
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                route_url = route.url.format(pk=pk)
                url = self.build_url(prefix, route_url)
                view = viewset.as_view(
                    mapping,
                    basename=basename,
                    route_detail=route.detail,
                    route_action=route.name,
                )
                urls.append(path(url, view, name=route.name))

        return urls

    def get_routes(self, viewset):
        return [*self.routes, *self.get_extra_routes(viewset)]

    def get_extra_routes(self, viewset):
        if not hasattr(viewset, "get_extra_actions"):
            return []

        routes = []

        for extra_action in viewset.get_extra_actions():
            url = extra_action.url_path
            if extra_action.detail:
                url = "{pk}/%s" % url

            routes.append(
                Route(
                    url=url,
                    mapping=extra_action.mapping,
                    name=extra_action.url_name,
                    detail=extra_action.detail,
                )
            )

        return routes

    def get_pk_path(self, viewset):
        pk_url_kwarg = getattr(viewset, "pk_url_kwarg", "pk")
        return "<int:%s>" % pk_url_kwarg

    def get_method_map(self, viewset, mapping):
        return {
            method: action
            for method, action in mapping.items()
            if hasattr(viewset, action)
        }

    def build_url(self, prefix, route_url):
        if prefix and route_url:
            url = f"{prefix}/{route_url}"
        else:
            url = prefix or route_url

        if url:
            return url + "/"
        return ""
