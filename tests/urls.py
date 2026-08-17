# router
from django_htmx_base.routers import HtmxRouter

# viewsets
from tests.viewsets import TestBaseModelViewSet
from tests.viewsets import TestCustomFormViewSet

router = HtmxRouter()
router.register("test-base-models", TestBaseModelViewSet)
router.register("test-custom-form", TestCustomFormViewSet, basename="testform")

urlpatterns = router.urls
