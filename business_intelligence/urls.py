from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TableauBordViewSet, WidgetTableauBordViewSet,
    DataWarehouseSnapshotViewSet,
    RapportBIViewSet,
    DatamartFinanceViewSet, DatamartSEViewSet,
    DatamartRHViewSet, DatamartCourrierViewSet,
    DatamartGEDViewSet, DatamartRisqueViewSet,
    ConnecteurBIViewSet, KPIPersonnaliseViewSet,
    dashboard_bi,
)

router = DefaultRouter()

# M34 — Tableaux de bord
router.register(r'tableaux-bord', TableauBordViewSet, basename='tableau-bord')
router.register(r'widgets', WidgetTableauBordViewSet, basename='widget')

# M35 — Business Intelligence
router.register(r'snapshots', DataWarehouseSnapshotViewSet, basename='dw-snapshot')
router.register(r'rapports', RapportBIViewSet, basename='rapport-bi')
router.register(r'datamart-finances', DatamartFinanceViewSet, basename='datamart-finance')
router.register(r'datamart-se', DatamartSEViewSet, basename='datamart-se')
router.register(r'datamart-rh', DatamartRHViewSet, basename='datamart-rh')
router.register(r'datamart-courriers', DatamartCourrierViewSet, basename='datamart-courrier')
router.register(r'datamart-ged', DatamartGEDViewSet, basename='datamart-ged')
router.register(r'datamart-risques', DatamartRisqueViewSet, basename='datamart-risque')
router.register(r'connecteurs', ConnecteurBIViewSet, basename='connecteur-bi')
router.register(r'kpis', KPIPersonnaliseViewSet, basename='kpi-personnalise')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_bi, name='dashboard-bi'),
]
