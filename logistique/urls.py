from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehiculeViewSet, MissionVehiculeViewSet, EntretienVehiculeViewSet,
    EquipementViewSet,
    MagasinViewSet,
    ArticleStockViewSet, LigneStockViewSet, MouvementStockViewSet,
    dashboard_logistique,
)

router = DefaultRouter()

# M38 — Parc automobile
router.register(r'vehicules', VehiculeViewSet, basename='vehicule')
router.register(r'missions-vehicules', MissionVehiculeViewSet, basename='mission-vehicule')
router.register(r'entretiens-vehicules', EntretienVehiculeViewSet, basename='entretien-vehicule')

# M38 — Équipements
router.register(r'equipements', EquipementViewSet, basename='equipement')

# M38 — Stocks
router.register(r'magasins', MagasinViewSet, basename='magasin')
router.register(r'articles-stock', ArticleStockViewSet, basename='article-stock')
router.register(r'lignes-stock', LigneStockViewSet, basename='ligne-stock')
router.register(r'mouvements-stock', MouvementStockViewSet, basename='mouvement-stock')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_logistique, name='dashboard-logistique'),
]
