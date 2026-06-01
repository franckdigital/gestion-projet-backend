from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourrierEntrantViewSet, CourrierSortantViewSet,
    CircuitValidationViewSet, EtapeCircuitViewSet,
    ParapheurViewSet, VisaParapheurViewSet, DiligenceViewSet,
    ModeleCourrierSortantViewSet, dashboard_courrier,
)

router = DefaultRouter()
# M27 — Courrier
router.register(r'entrants', CourrierEntrantViewSet, basename='courrier-entrant')
router.register(r'sortants', CourrierSortantViewSet, basename='courrier-sortant')
router.register(r'modeles', ModeleCourrierSortantViewSet, basename='modele-courrier')
# Parapheur
router.register(r'circuits', CircuitValidationViewSet, basename='circuit-validation')
router.register(r'etapes-circuit', EtapeCircuitViewSet, basename='etape-circuit')
router.register(r'parapheurs', ParapheurViewSet, basename='parapheur')
router.register(r'visas', VisaParapheurViewSet, basename='visa-parapheur')
# Diligences
router.register(r'diligences', DiligenceViewSet, basename='diligence')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_courrier, name='dashboard-courrier'),
]
