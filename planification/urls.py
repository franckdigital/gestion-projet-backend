from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# M08 - Cadre Logique
router.register('cadres-logiques', views.CadreLogiqueViewSet, basename='cadre-logique')
router.register('elements-cadre', views.ElementCadreLogiqueViewSet, basename='element-cadre')

# M09 - SWOT
router.register('analyses-swot', views.AnalyseSWOTViewSet, basename='analyse-swot')
router.register('elements-swot', views.ElementSWOTViewSet, basename='element-swot')
router.register('strategies-swot', views.StrategieSWOTViewSet, basename='strategie-swot')

# M10 - TDR
router.register('tdrs', views.TDRViewSet, basename='tdr')

# M11 - Plans d'Actions
router.register('plans-action', views.PlanActionViewSet, basename='plan-action')
router.register('actions', views.ActionPlanItemViewSet, basename='action')

# M12 - Programmes d'Activites
router.register('programmes-activites', views.ProgrammeActivitesViewSet, basename='programme-activites')
router.register('activites-pa', views.ActivitePAViewSet, basename='activite-pa')

# Plans de travail operationnels
router.register('plans-travail', views.PlanTravailViewSet, basename='plan-travail')
router.register('activites', views.ActiviteViewSet, basename='activite')
router.register('jalons', views.JalonViewSet, basename='jalon')

urlpatterns = [
    path('', include(router.urls)),
]
