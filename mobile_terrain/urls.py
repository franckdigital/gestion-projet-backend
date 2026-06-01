from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SessionTerrainViewSet, CollecteTerrainViewSet, PointageTerrainViewSet,
    SynchronisationMobileViewSet, QRCodeScanViewSet, dashboard_mobile,
)

router = DefaultRouter()
router.register(r'sessions', SessionTerrainViewSet, basename='session-terrain')
router.register(r'collectes', CollecteTerrainViewSet, basename='collecte-terrain')
router.register(r'pointages', PointageTerrainViewSet, basename='pointage-terrain')
router.register(r'synchronisations', SynchronisationMobileViewSet, basename='synchronisation-mobile')
router.register(r'qr-scans', QRCodeScanViewSet, basename='qr-scan')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_mobile, name='dashboard-mobile'),
]
