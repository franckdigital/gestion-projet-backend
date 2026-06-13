from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeProjetViewSet, AffectationRHViewSet,
    FeuilleTempsViewSet, LigneFeuilleTempsViewSet,
    EvaluationPerformanceViewSet, BesoinFormationViewSet,
    DemandeCongeViewSet, DemandeAbsenceViewSet, OccurrenceSpecialeViewSet,
    dashboard_rh,
)

router = DefaultRouter()

# Employés
router.register(r'employes', EmployeProjetViewSet, basename='employe')

# Affectations
router.register(r'affectations', AffectationRHViewSet, basename='affectation')

# Feuilles de temps
router.register(r'feuilles-temps', FeuilleTempsViewSet, basename='feuille-temps')
router.register(r'lignes-feuille-temps', LigneFeuilleTempsViewSet, basename='ligne-feuille-temps')

# Évaluations de performance
router.register(r'evaluations', EvaluationPerformanceViewSet, basename='evaluation')

# Besoins de formation
router.register(r'besoins-formation', BesoinFormationViewSet, basename='besoin-formation')

# Congés et absences
router.register(r'conges', DemandeCongeViewSet, basename='demande-conge')
router.register(r'absences', DemandeAbsenceViewSet, basename='demande-absence')
router.register(r'occurrences-speciales', OccurrenceSpecialeViewSet, basename='occurrence-speciale')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_rh, name='dashboard-rh'),
]
