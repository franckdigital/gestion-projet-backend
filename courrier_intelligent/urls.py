from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompteEmailViewSet, EmailViewSet, PieceJointeViewSet,
    ActionEmailViewSet, EtiquetteViewSet, LienEmailViewSet,
    RegleClassificationViewSet, dashboard_courrier_intelligent,
)

router = DefaultRouter()
router.register(r'comptes', CompteEmailViewSet, basename='compte-email')
router.register(r'emails', EmailViewSet, basename='email')
router.register(r'pieces-jointes', PieceJointeViewSet, basename='pj-email')
router.register(r'actions', ActionEmailViewSet, basename='action-email')
router.register(r'etiquettes', EtiquetteViewSet, basename='etiquette-email')
router.register(r'liens', LienEmailViewSet, basename='lien-email')
router.register(r'regles', RegleClassificationViewSet, basename='regle-classification')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_courrier_intelligent, name='dashboard-courrier-intelligent'),
]
