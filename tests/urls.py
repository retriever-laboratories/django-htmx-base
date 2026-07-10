from django_htmx_base.routers import HtmxRouter
from tests.viewsets import TestBaseModelViewSet

router = HtmxRouter()
router.register("test-base-models", TestBaseModelViewSet)

urlpatterns = router.urls
