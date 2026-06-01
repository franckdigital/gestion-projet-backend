from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Role, Permission, UserSession, LoginAttempt, AuditLog, OTPCode


class PermissionInline(admin.TabularInline):
    model = Permission
    extra = 0


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'type_role', 'actif', 'est_systeme', 'nb_utilisateurs']
    list_filter = ['type_role', 'actif', 'est_systeme']
    search_fields = ['nom', 'code']
    inlines = [PermissionInline]
    readonly_fields = ['created_at', 'updated_at']

    def nb_utilisateurs(self, obj):
        return obj.utilisateurs.count()
    nb_utilisateurs.short_description = 'Utilisateurs'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'matricule', 'telephone', 'telephone_mobile', 'photo', 'langue')
        }),
        (_('Informations professionnelles'), {
            'fields': ('poste', 'fonction', 'date_embauche', 'manager',
                       'organisation', 'direction', 'service', 'site')
        }),
        (_('Rôles'), {'fields': ('roles',)}),
        (_('MFA'), {'fields': ('mfa_enabled', 'mfa_method')}),
        (_('Sécurité'), {
            'fields': ('failed_login_attempts', 'locked_until', 'last_login_ip', 'must_change_password')
        }),
        (_('Permissions système'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'first_name', 'last_name', 'password1', 'password2')}),
    )
    list_display = ['email', 'first_name', 'last_name', 'matricule', 'is_active', 'mfa_enabled', 'date_joined']
    list_filter = ['is_active', 'mfa_enabled', 'organisation', 'direction']
    search_fields = ['email', 'first_name', 'last_name', 'matricule']
    ordering = ['last_name', 'first_name']
    filter_horizontal = ['roles', 'groups', 'user_permissions']
    readonly_fields = ['last_login', 'date_joined', 'last_login_ip']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'is_active', 'last_activity', 'created_at']
    list_filter = ['is_active']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['token', 'created_at']


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['email_tente', 'resultat', 'ip_address', 'created_at']
    list_filter = ['resultat']
    search_fields = ['email_tente', 'ip_address']
    readonly_fields = ['created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'module', 'objet_repr', 'ip_address', 'created_at']
    list_filter = ['action', 'module']
    search_fields = ['user__email', 'objet_repr', 'ip_address']
    readonly_fields = ['created_at']
