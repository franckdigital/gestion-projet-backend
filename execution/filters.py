import django_filters
from django.utils import timezone
from .models import (
    ActiviteExecution, Tache, Livrable, Reunion, Mission,
)


class ActiviteExecutionFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr='icontains')
    intitule = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=ActiviteExecution.STATUT_CHOICES)
    priorite = django_filters.ChoiceFilter(choices=ActiviteExecution.PRIORITE_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    parent = django_filters.NumberFilter(field_name='parent__id')
    sans_parent = django_filters.BooleanFilter(field_name='parent', lookup_expr='isnull')
    date_debut_apres = django_filters.DateFilter(field_name='date_debut_prevue', lookup_expr='gte')
    date_debut_avant = django_filters.DateFilter(field_name='date_debut_prevue', lookup_expr='lte')
    date_fin_apres = django_filters.DateFilter(field_name='date_fin_prevue', lookup_expr='gte')
    date_fin_avant = django_filters.DateFilter(field_name='date_fin_prevue', lookup_expr='lte')
    budget_min = django_filters.NumberFilter(field_name='budget_prevu', lookup_expr='gte')
    budget_max = django_filters.NumberFilter(field_name='budget_prevu', lookup_expr='lte')
    taux_min = django_filters.NumberFilter(field_name='taux_avancement', lookup_expr='gte')
    taux_max = django_filters.NumberFilter(field_name='taux_avancement', lookup_expr='lte')
    en_retard = django_filters.BooleanFilter(method='filter_en_retard')

    class Meta:
        model = ActiviteExecution
        fields = ['statut', 'priorite', 'projet', 'programme', 'responsable']

    def filter_en_retard(self, queryset, name, value):
        if value:
            return queryset.filter(
                date_fin_prevue__lt=timezone.now().date()
            ).exclude(statut__in=['terminee', 'annulee', 'archivee'])
        return queryset


class TacheFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr='icontains')
    titre = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=Tache.STATUT_CHOICES)
    priorite = django_filters.ChoiceFilter(choices=Tache.PRIORITE_CHOICES)
    activite = django_filters.NumberFilter(field_name='activite__id')
    projet = django_filters.NumberFilter(field_name='activite__projet__id')
    assignee = django_filters.NumberFilter(field_name='assignee__id')
    parent = django_filters.NumberFilter(field_name='parent__id')
    sans_parent = django_filters.BooleanFilter(field_name='parent', lookup_expr='isnull')
    date_echeance_apres = django_filters.DateFilter(field_name='date_echeance', lookup_expr='gte')
    date_echeance_avant = django_filters.DateFilter(field_name='date_echeance', lookup_expr='lte')
    en_retard = django_filters.BooleanFilter(method='filter_en_retard')

    class Meta:
        model = Tache
        fields = ['statut', 'priorite', 'activite', 'assignee']

    def filter_en_retard(self, queryset, name, value):
        if value:
            return queryset.filter(
                date_echeance__lt=timezone.now().date()
            ).exclude(statut__in=['terminee', 'annulee'])
        return queryset


class LivrableFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr='icontains')
    titre = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=Livrable.STATUT_CHOICES)
    type_livrable = django_filters.ChoiceFilter(choices=Livrable.TYPE_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    activite = django_filters.NumberFilter(field_name='activite__id')
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    date_prevue_apres = django_filters.DateFilter(field_name='date_prevue', lookup_expr='gte')
    date_prevue_avant = django_filters.DateFilter(field_name='date_prevue', lookup_expr='lte')
    en_retard = django_filters.BooleanFilter(method='filter_en_retard')

    class Meta:
        model = Livrable
        fields = ['statut', 'type_livrable', 'projet', 'activite', 'responsable']

    def filter_en_retard(self, queryset, name, value):
        if value:
            return queryset.filter(
                date_prevue__lt=timezone.now().date()
            ).exclude(statut__in=['valide', 'publie', 'archive'])
        return queryset


class ReunionFilter(django_filters.FilterSet):
    reference = django_filters.CharFilter(lookup_expr='icontains')
    objet = django_filters.CharFilter(lookup_expr='icontains')
    type_reunion = django_filters.ChoiceFilter(choices=Reunion.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Reunion.STATUT_CHOICES)
    plateforme = django_filters.ChoiceFilter(choices=Reunion.PLATEFORME_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    organisateur = django_filters.NumberFilter(field_name='organisateur__id')
    date_apres = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    mois = django_filters.NumberFilter(field_name='date', lookup_expr='month')
    annee = django_filters.NumberFilter(field_name='date', lookup_expr='year')

    class Meta:
        model = Reunion
        fields = ['type_reunion', 'statut', 'plateforme', 'projet', 'programme', 'organisateur']


class MissionFilter(django_filters.FilterSet):
    reference = django_filters.CharFilter(lookup_expr='icontains')
    objet = django_filters.CharFilter(lookup_expr='icontains')
    type_mission = django_filters.ChoiceFilter(choices=Mission.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Mission.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    demandeur = django_filters.NumberFilter(field_name='demandeur__id')
    destination = django_filters.CharFilter(lookup_expr='icontains')
    date_debut_apres = django_filters.DateFilter(field_name='date_debut', lookup_expr='gte')
    date_fin_avant = django_filters.DateFilter(field_name='date_fin', lookup_expr='lte')
    budget_min = django_filters.NumberFilter(field_name='budget_prevu', lookup_expr='gte')
    budget_max = django_filters.NumberFilter(field_name='budget_prevu', lookup_expr='lte')

    class Meta:
        model = Mission
        fields = ['type_mission', 'statut', 'projet', 'programme', 'demandeur']
