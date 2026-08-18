# router
from django_htmx_base.routers import HtmxRouter
from tests.viewsets import TestBaseModelUserTrackedViewSet

# viewsets
from tests.viewsets import TestBaseModelViewSet
from tests.viewsets import TestCustomFormViewSet

router = HtmxRouter()
router.register("test-base-models", TestBaseModelViewSet)
router.register("test-base-models-user-tracked", TestBaseModelUserTrackedViewSet)
router.register("test-custom-form", TestCustomFormViewSet, basename="testform")

urlpatterns = router.urls
