from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ZoneSIGViewSet, CoucheCartographiqueViewSet,
    PointCartographieViewSet, InfrastructureSIGViewSet,
    CarteSIGViewSet, dashboard_sig,
)

router = DefaultRouter()

# M41 — SIG avancé
router.register(r'zones', ZoneSIGViewSet, basename='zone-sig')
router.register(r'couches', CoucheCartographiqueViewSet, basename='couche-cartographique')
router.register(r'points', PointCartographieViewSet, basename='point-cartographie')
router.register(r'infrastructures', InfrastructureSIGViewSet, basename='infrastructure-sig')
router.register(r'cartes', CarteSIGViewSet, basename='carte-sig')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_sig, name='dashboard-sig'),
]
