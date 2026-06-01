from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NonConformiteViewSet, ActionQualiteViewSet,
    AuditInterneViewSet, IndicateurQualiteViewSet,
    dashboard_qualite,
)

router = DefaultRouter()
router.register(r'non-conformites', NonConformiteViewSet, basename='non-conformite')
router.register(r'actions', ActionQualiteViewSet, basename='action-qualite')
router.register(r'audits', AuditInterneViewSet, basename='audit-interne')
router.register(r'indicateurs', IndicateurQualiteViewSet, basename='indicateur-qualite')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_qualite, name='dashboard-qualite'),
]
