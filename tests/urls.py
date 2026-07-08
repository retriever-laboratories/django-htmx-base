from django_htmx_base.routers import HtmxRouter
from django_htmx_base.viewsets import HtmxViewSet
from tests.models import Article


class ArticleViewSet(HtmxViewSet):
    model = Article


router = HtmxRouter()
router.register("articles", ArticleViewSet)

urlpatterns = router.urls
