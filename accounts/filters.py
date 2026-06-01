import django_filters
from .models import User, Role, AuditLog, LoginAttempt


class UserFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(method='filter_nom', label='Nom ou prénom')
    email = django_filters.CharFilter(lookup_expr='icontains')
    matricule = django_filters.CharFilter(lookup_expr='icontains')
    organisation = django_filters.NumberFilter(field_name='organisation__id')
    direction = django_filters.NumberFilter(field_name='direction__id')
    service = django_filters.NumberFilter(field_name='service__id')
    site = django_filters.NumberFilter(field_name='site__id')
    role = django_filters.CharFilter(method='filter_role', label='Code rôle')
    is_active = django_filters.BooleanFilter()
    mfa_enabled = django_filters.BooleanFilter()
    date_embauche_apres = django_filters.DateFilter(field_name='date_embauche', lookup_expr='gte')
    date_embauche_avant = django_filters.DateFilter(field_name='date_embauche', lookup_expr='lte')

    class Meta:
        model = User
        fields = ['email', 'is_active', 'mfa_enabled', 'organisation', 'direction', 'service', 'site']

    def filter_nom(self, queryset, name, value):
        return queryset.filter(
            models.Q(first_name__icontains=value) | models.Q(last_name__icontains=value)
        )

    def filter_role(self, queryset, name, value):
        return queryset.filter(roles__code=value)


import django_filters
from django.db import models as django_models


class UserFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(method='filter_nom')
    email = django_filters.CharFilter(lookup_expr='icontains')
    matricule = django_filters.CharFilter(lookup_expr='icontains')
    role = django_filters.CharFilter(method='filter_role')
    organisation = django_filters.NumberFilter(field_name='organisation__id')
    direction = django_filters.NumberFilter(field_name='direction__id')
    service = django_filters.NumberFilter(field_name='service__id')
    is_active = django_filters.BooleanFilter()
    verrouille = django_filters.BooleanFilter(method='filter_verrouille')

    class Meta:
        model = User
        fields = ['email', 'is_active', 'mfa_enabled', 'organisation', 'direction', 'service']

    def filter_nom(self, queryset, name, value):
        return queryset.filter(
            django_models.Q(first_name__icontains=value) | django_models.Q(last_name__icontains=value)
        )

    def filter_role(self, queryset, name, value):
        return queryset.filter(roles__code=value)

    def filter_verrouille(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(locked_until__gt=timezone.now())
        return queryset.filter(
            django_models.Q(locked_until__isnull=True) | django_models.Q(locked_until__lte=timezone.now())
        )


class RoleFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    type_role = django_filters.ChoiceFilter(choices=Role.TYPE_CHOICES)
    actif = django_filters.BooleanFilter()

    class Meta:
        model = Role
        fields = ['nom', 'type_role', 'actif', 'est_systeme']


class AuditLogFilter(django_filters.FilterSet):
    user = django_filters.NumberFilter(field_name='user__id')
    action = django_filters.ChoiceFilter(choices=AuditLog.ACTION_CHOICES)
    module = django_filters.CharFilter(lookup_expr='exact')
    date_debut = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_fin = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = AuditLog
        fields = ['user', 'action', 'module']


class LoginAttemptFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(field_name='email_tente', lookup_expr='icontains')
    resultat = django_filters.ChoiceFilter(choices=LoginAttempt.RESULT_CHOICES)
    ip = django_filters.CharFilter(field_name='ip_address', lookup_expr='icontains')
    date_debut = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_fin = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = LoginAttempt
        fields = ['resultat']
