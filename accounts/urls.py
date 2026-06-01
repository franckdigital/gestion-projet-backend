from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='user')
router.register('roles', views.RoleViewSet, basename='role')
router.register('sessions', views.UserSessionViewSet, basename='session')
router.register('login-attempts', views.LoginAttemptViewSet, basename='login-attempt')
router.register('audit', views.AuditLogViewSet, basename='audit')

urlpatterns = [
    # Auth
    path('login/', views.login, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', views.logout, name='logout'),
    path('verify-otp/', views.verify_otp, name='verify-otp'),

    # Password
    path('password/reset/', views.password_reset_request, name='password-reset-request'),
    path('password/reset/confirm/', views.password_reset_confirm, name='password-reset-confirm'),
    path('password/change/', views.change_password, name='change-password'),

    # Profile
    path('me/', views.me, name='me'),

    # MFA
    path('mfa/setup/', views.mfa_setup, name='mfa-setup'),
    path('mfa/verify-setup/', views.mfa_verify_setup, name='mfa-verify-setup'),
    path('mfa/disable/', views.mfa_disable, name='mfa-disable'),

    # Dashboard
    path('dashboard/securite/', views.dashboard_securite, name='dashboard-securite'),

    # Router (users, roles, sessions, audit, login-attempts)
    path('', include(router.urls)),
]
