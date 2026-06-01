from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlanPassationMarcheViewSet,
    DemandeAchatViewSet,
    AppelOffreViewSet,
    SoumissionnaireOffreViewSet,
    ContratMarcheViewSet,
    AvenantContratViewSet,
    dashboard_marches,
)

router = DefaultRouter()

# Plans de passation
router.register(r'plans-passation', PlanPassationMarcheViewSet, basename='plan-passation')

# Demandes d'achat
router.register(r'demandes-achat', DemandeAchatViewSet, basename='demande-achat')

# Appels d'offres
router.register(r'appels-offre', AppelOffreViewSet, basename='appel-offre')

# Soumissionnaires
router.register(r'soumissionnaires', SoumissionnaireOffreViewSet, basename='soumissionnaire')

# Contrats
router.register(r'contrats', ContratMarcheViewSet, basename='contrat-marche')

# Avenants
router.register(r'avenants', AvenantContratViewSet, basename='avenant-contrat')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_marches, name='dashboard-marches'),
]
