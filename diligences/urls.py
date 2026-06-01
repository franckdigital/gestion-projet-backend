from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiligenceViewSet, SuiviDiligenceViewSet, RelanceDiligenceViewSet

router = DefaultRouter()
router.register(r'diligences', DiligenceViewSet, basename='diligence')
router.register(r'suivis', SuiviDiligenceViewSet, basename='suivi-diligence')
router.register(r'relances', RelanceDiligenceViewSet, basename='relance-diligence')

urlpatterns = [path('', include(router.urls))]
