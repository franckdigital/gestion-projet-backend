from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CanalViewSet, MessageViewSet, NotificationViewSet,
    PreferenceNotificationViewSet, ActiviteRecenteViewSet, GroupeTravailViewSet,
    EvenementViewSet, ParticipantEvenementViewSet, DepenseEvenementViewSet,
    dashboard_collaboration, envoyer_notification_bulk,
)

router = DefaultRouter()
# M28 — Messagerie
router.register(r'canaux', CanalViewSet, basename='canal')
router.register(r'messages', MessageViewSet, basename='message')
# Notifications
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'preferences-notif', PreferenceNotificationViewSet, basename='preference-notif')
# Centre d'activités & groupes
router.register(r'activites-recentes', ActiviteRecenteViewSet, basename='activite-recente')
router.register(r'groupes', GroupeTravailViewSet, basename='groupe-travail')
# M43 — Événements
router.register(r'evenements', EvenementViewSet, basename='evenement')
router.register(r'participants-evenements', ParticipantEvenementViewSet, basename='participant-evenement')
router.register(r'depenses-evenements', DepenseEvenementViewSet, basename='depense-evenement')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_collaboration, name='dashboard-collaboration'),
    path('notifications/bulk/', envoyer_notification_bulk, name='notif-bulk'),
]
