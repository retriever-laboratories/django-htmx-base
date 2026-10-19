# router
from django_htmx_base.routers import HtmxRouter

# viewsets
from tests.viewsets import TestBaseModelViewSet
from tests.viewsets import TestCustomFormSetViewSet
from tests.viewsets import TestCustomFormViewSet
from tests.viewsets import TestToastViewSet

router = HtmxRouter()
router.register("test-base-models", TestBaseModelViewSet)
router.register("test-custom-form", TestCustomFormViewSet, basename="testform")
router.register("test-custom-formset", TestCustomFormSetViewSet, basename="testformset")
router.register("test-toast", TestToastViewSet, basename="testtoast")

urlpatterns = router.urls
