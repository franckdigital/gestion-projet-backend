from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PartenaireViewSet, ContactPartenaireViewSet, LiaisonProjetPartenaireViewSet,
    ConventionViewSet, RenouvellementConventionViewSet,
    AccesPortailPartenaireViewSet, DepotDocumentPortailViewSet,
    dashboard_partenaires,
)

router = DefaultRouter()
router.register(r'partenaires', PartenaireViewSet, basename='partenaire')
router.register(r'contacts', ContactPartenaireViewSet, basename='contact-partenaire')
router.register(r'liaisons-projet', LiaisonProjetPartenaireViewSet, basename='liaison-projet-partenaire')
router.register(r'conventions', ConventionViewSet, basename='convention')
router.register(r'renouvellements', RenouvellementConventionViewSet, basename='renouvellement-convention')
router.register(r'acces-portail', AccesPortailPartenaireViewSet, basename='acces-portail-partenaire')
router.register(r'depots', DepotDocumentPortailViewSet, basename='depot-document-portail')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_partenaires, name='dashboard-partenaires'),
]
