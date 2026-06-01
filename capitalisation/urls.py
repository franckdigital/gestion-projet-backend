from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FicheCapitalisationViewSet, EntreeBibliothequeViewSet,
    CommentaireFicheViewSet, CentreConnaissanceViewSet,
    dashboard_capitalisation,
)

router = DefaultRouter()

# M45 — Capitalisation des connaissances
router.register(r'fiches', FicheCapitalisationViewSet, basename='fiche-capitalisation')
router.register(r'bibliotheque', EntreeBibliothequeViewSet, basename='entree-bibliotheque')
router.register(r'commentaires', CommentaireFicheViewSet, basename='commentaire-fiche')
router.register(r'centres', CentreConnaissanceViewSet, basename='centre-connaissance')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_capitalisation, name='dashboard-capitalisation'),
]
