from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IndicateurViewSet, ValeurCiblePeriodeViewSet, CollecteIndicateurViewSet,
    AlerteIndicateurViewSet,
    FormulaireDynamiqueViewSet, ChampFormulaireViewSet,
    SoumissionFormulaireViewSet,
    EnqueteViewSet, SectionEnqueteViewSet, QuestionEnqueteViewSet, ReponseEnqueteViewSet,
    CadreResultatsViewSet, NiveauResultatViewSet, TheorieChangementViewSet,
    EvaluationViewSet, CritereEvaluationViewSet, LeconApprisViewSet,
    RapportSEViewSet, AnalysePredictiveViewSet, PointSIGViewSet,
    RegistreRisqueViewSet, PlanMitigationViewSet, SuiviRisqueViewSet, AlerteRisqueViewSet,
    dashboard_se, dashboard_direction,
)

router = DefaultRouter()

# M17 — Indicateurs
router.register(r'indicateurs', IndicateurViewSet, basename='indicateur')
router.register(r'cibles-periodes', ValeurCiblePeriodeViewSet, basename='cible-periode')
router.register(r'collectes', CollecteIndicateurViewSet, basename='collecte-indicateur')
router.register(r'alertes', AlerteIndicateurViewSet, basename='alerte-indicateur')

# M18 — Formulaires dynamiques
router.register(r'formulaires', FormulaireDynamiqueViewSet, basename='formulaire')
router.register(r'champs-formulaire', ChampFormulaireViewSet, basename='champ-formulaire')
router.register(r'soumissions', SoumissionFormulaireViewSet, basename='soumission')

# M19 — Enquêtes
router.register(r'enquetes', EnqueteViewSet, basename='enquete')
router.register(r'sections-enquete', SectionEnqueteViewSet, basename='section-enquete')
router.register(r'questions-enquete', QuestionEnqueteViewSet, basename='question-enquete')
router.register(r'reponses-enquete', ReponseEnqueteViewSet, basename='reponse-enquete')

# M20 — Cadre de résultats et évaluations
router.register(r'cadres-resultats', CadreResultatsViewSet, basename='cadre-resultats')
router.register(r'niveaux-resultats', NiveauResultatViewSet, basename='niveau-resultat')
router.register(r'theories-changement', TheorieChangementViewSet, basename='theorie-changement')
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')
router.register(r'criteres-evaluation', CritereEvaluationViewSet, basename='critere-evaluation')
router.register(r'lecons-apprises', LeconApprisViewSet, basename='lecon-apprise')

# Rapports & IA
router.register(r'rapports', RapportSEViewSet, basename='rapport-se')
router.register(r'analyses-predictives', AnalysePredictiveViewSet, basename='analyse-predictive')

# SIG
router.register(r'sig/points', PointSIGViewSet, basename='point-sig')

# M29 — Risques
router.register(r'risques', RegistreRisqueViewSet, basename='registre-risque')
router.register(r'risques-plans', PlanMitigationViewSet, basename='plan-mitigation')
router.register(r'risques-suivis', SuiviRisqueViewSet, basename='suivi-risque')
router.register(r'risques-alertes', AlerteRisqueViewSet, basename='alerte-risque')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_se, name='dashboard-se'),
    path('dashboard/direction/', dashboard_direction, name='dashboard-direction'),
]
