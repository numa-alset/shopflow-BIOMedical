from rest_framework.routers import DefaultRouter

from .views import ProductVariantViewSet, ProductViewSet


router = DefaultRouter()

router.register(
    r'variants',
    ProductVariantViewSet,
    basename='product-variant'
)

router.register(
    r'',
    ProductViewSet,
    basename='product'
)

urlpatterns = router.urls