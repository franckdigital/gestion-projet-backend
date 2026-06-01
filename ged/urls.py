from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategorieViewSet, DocumentViewSet, VersionDocumentViewSet, DossierDocumentViewSet,
    WorkflowValidationViewSet, SignatureViewSet, LienPartageViewSet,
    AccesDocumentViewSet, AuditDocumentViewSet, CommentaireDocumentViewSet,
    PlanConservationViewSet, BoiteArchiveViewSet, DocumentArchiveViewSet,
    DemandeDestructionViewSet, ModeleDocumentViewSet, EntreeBibliothequeViewSet,
    dashboard_ged, rapport_conformite,
)

router = DefaultRouter()

# M24 — GED
router.register(r'categories', CategorieViewSet, basename='categorie-ged')
router.register(r'documents', DocumentViewSet, basename='document-ged')
router.register(r'versions', VersionDocumentViewSet, basename='version-document')
router.register(r'dossiers', DossierDocumentViewSet, basename='dossier-document')
router.register(r'workflow-validations', WorkflowValidationViewSet, basename='workflow-validation-ged')
router.register(r'signatures', SignatureViewSet, basename='signature-electronique')
router.register(r'liens-partage', LienPartageViewSet, basename='lien-partage')
router.register(r'acces', AccesDocumentViewSet, basename='acces-document')
router.register(r'audit', AuditDocumentViewSet, basename='audit-document')
router.register(r'commentaires', CommentaireDocumentViewSet, basename='commentaire-document')

# M25 — Archivage
router.register(r'plans-conservation', PlanConservationViewSet, basename='plan-conservation')
router.register(r'boites-archives', BoiteArchiveViewSet, basename='boite-archive')
router.register(r'documents-archives', DocumentArchiveViewSet, basename='document-archive')
router.register(r'destructions', DemandeDestructionViewSet, basename='demande-destruction')

# Bibliothèque et modèles
router.register(r'modeles', ModeleDocumentViewSet, basename='modele-document')
router.register(r'bibliotheque', EntreeBibliothequeViewSet, basename='entree-bibliotheque')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_ged, name='dashboard-ged'),
    path('conformite/', rapport_conformite, name='rapport-conformite-ged'),
]
