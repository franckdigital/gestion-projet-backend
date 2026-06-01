from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('organisations', views.OrganisationViewSet, basename='organisation')
router.register('directions', views.DirectionViewSet, basename='direction')
router.register('sous-directions', views.SousDirectionViewSet, basename='sous-direction')
router.register('services', views.ServiceViewSet, basename='service')
router.register('sites', views.SiteViewSet, basename='site')
router.register('partenaires', views.PartenaireViewSet, basename='partenaire')
router.register('bailleurs', views.BailleurViewSet, basename='bailleur')
router.register('comites', views.ComiteDirecteurViewSet, basename='comite')

urlpatterns = [
    path('dashboard/', views.dashboard_gouvernance, name='dashboard-gouvernance'),
    path('', include(router.urls)),
]
