from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvenementViewSet, ParticipantViewSet, DepenseEvenementViewSet

router = DefaultRouter()
router.register(r'evenements', EvenementViewSet, basename='evenement')
router.register(r'participants', ParticipantViewSet, basename='participant-evenement')
router.register(r'depenses', DepenseEvenementViewSet, basename='depense-evenement')

urlpatterns = [path('', include(router.urls))]
