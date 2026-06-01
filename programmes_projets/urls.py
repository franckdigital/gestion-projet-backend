from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('zones-intervention', views.ZoneInterventionViewSet, basename='zone-intervention')
router.register('programmes', views.ProgrammeViewSet, basename='programme')
router.register('objectifs-programme', views.ObjectifProgrammeViewSet, basename='objectif-programme')
router.register('documents-programme', views.DocumentProgrammeViewSet, basename='document-programme')
router.register('partenaires-programme', views.PartenaireProgrammeViewSet, basename='partenaire-programme')
router.register('projets', views.ProjetViewSet, basename='projet')
router.register('membres-equipe', views.MembreEquipeViewSet, basename='membre-equipe')
router.register('risques', views.RisqueViewSet, basename='risque')
router.register('livrables', views.LivrableViewSet, basename='livrable')
router.register('jalons', views.JalonProjetViewSet, basename='jalon')

urlpatterns = [
    path('portefeuille/', views.portefeuille_dashboard, name='portefeuille-dashboard'),
    path('', include(router.urls)),
]
