from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ActiviteExecutionViewSet, AffectationRessourceViewSet,
    DependanceActiviteViewSet, RapportActiviteViewSet,
    TacheViewSet, ChecklistItemViewSet, DependanceTacheViewSet,
    HistoriqueTacheViewSet, CommentaireTacheViewSet,
    LivrableViewSet, VersionLivrableViewSet, CommentaireLivrableViewSet,
    ReunionViewSet, ParticipantReunionViewSet, PointOrdreJourViewSet,
    CompteRenduViewSet, DecisionReunionViewSet, ActionReunionViewSet,
    MissionViewSet, MembreMissionViewSet, OrdreMissionViewSet,
    RapportMissionViewSet, RapportAvancementViewSet,
    dashboard_execution,
)

router = DefaultRouter()

# M13 — Activités
router.register(r'activites', ActiviteExecutionViewSet, basename='activite-execution')
router.register(r'affectations-ressources', AffectationRessourceViewSet, basename='affectation-ressource')
router.register(r'dependances-activites', DependanceActiviteViewSet, basename='dependance-activite')
router.register(r'rapports-activites', RapportActiviteViewSet, basename='rapport-activite')

# M14 — Tâches
router.register(r'taches', TacheViewSet, basename='tache')
router.register(r'checklist-items', ChecklistItemViewSet, basename='checklist-item')
router.register(r'dependances-taches', DependanceTacheViewSet, basename='dependance-tache')
router.register(r'historique-taches', HistoriqueTacheViewSet, basename='historique-tache')
router.register(r'commentaires-taches', CommentaireTacheViewSet, basename='commentaire-tache')

# M15 — Livrables
router.register(r'livrables', LivrableViewSet, basename='livrable')
router.register(r'versions-livrables', VersionLivrableViewSet, basename='version-livrable')
router.register(r'commentaires-livrables', CommentaireLivrableViewSet, basename='commentaire-livrable')

# M16 — Réunions
router.register(r'reunions', ReunionViewSet, basename='reunion')
router.register(r'participants-reunion', ParticipantReunionViewSet, basename='participant-reunion')
router.register(r'points-ordre-jour', PointOrdreJourViewSet, basename='point-ordre-jour')
router.register(r'comptes-rendus', CompteRenduViewSet, basename='compte-rendu')
router.register(r'decisions-reunion', DecisionReunionViewSet, basename='decision-reunion')
router.register(r'actions-reunion', ActionReunionViewSet, basename='action-reunion')

# M16 — Missions
router.register(r'missions', MissionViewSet, basename='mission')
router.register(r'membres-mission', MembreMissionViewSet, basename='membre-mission')
router.register(r'ordres-mission', OrdreMissionViewSet, basename='ordre-mission')
router.register(r'rapports-mission', RapportMissionViewSet, basename='rapport-mission')

# Rapports d'avancement
router.register(r'rapports-avancement', RapportAvancementViewSet, basename='rapport-avancement')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_execution, name='dashboard-execution'),
]
