from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationIAViewSet, MessageIAViewSet,
    GenerationDocumentViewSet,
    ModeleIAViewSet, AnalyseIAPredictiveViewSet,
    AlerteIAViewSet, RecommandationIAViewSet,
    JournalIAViewSet,
    dashboard_ia,
)

router = DefaultRouter()

# M31 — Assistant IA
router.register(r'conversations', ConversationIAViewSet, basename='conversation-ia')
router.register(r'messages', MessageIAViewSet, basename='message-ia')

# M32 — Génération documentaire
router.register(r'generations', GenerationDocumentViewSet, basename='generation-document')

# M33 — IA Prédictive
router.register(r'modeles', ModeleIAViewSet, basename='modele-ia')
router.register(r'analyses', AnalyseIAPredictiveViewSet, basename='analyse-ia')
router.register(r'alertes', AlerteIAViewSet, basename='alerte-ia')
router.register(r'recommandations', RecommandationIAViewSet, basename='recommandation-ia')
router.register(r'journal', JournalIAViewSet, basename='journal-ia')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_ia, name='dashboard-ia'),
]
