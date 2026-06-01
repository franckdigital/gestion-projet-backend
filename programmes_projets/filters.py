import django_filters
from django.db import models as dm
from .models import Programme, Projet, RisqueProjet


class ProgrammeFilter(django_filters.FilterSet):
    intitule = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=Programme.STATUT_CHOICES)
    organisation = django_filters.NumberFilter(field_name='organisation__id')
    bailleur = django_filters.NumberFilter(field_name='bailleur__id')
    coordonnateur = django_filters.NumberFilter(field_name='coordonnateur__id')
    date_debut_apres = django_filters.DateFilter(field_name='date_debut', lookup_expr='gte')
    date_debut_avant = django_filters.DateFilter(field_name='date_debut', lookup_expr='lte')
    date_fin_apres = django_filters.DateFilter(field_name='date_fin', lookup_expr='gte')
    date_fin_avant = django_filters.DateFilter(field_name='date_fin', lookup_expr='lte')
    budget_min = django_filters.NumberFilter(field_name='budget_total', lookup_expr='gte')
    budget_max = django_filters.NumberFilter(field_name='budget_total', lookup_expr='lte')

    class Meta:
        model = Programme
        fields = ['statut', 'organisation', 'bailleur', 'coordonnateur']


class ProjetFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=Projet.STATUT_CHOICES)
    priorite = django_filters.ChoiceFilter(choices=Projet.PRIORITE_CHOICES)
    programme = django_filters.NumberFilter(field_name='programme__id')
    organisation = django_filters.NumberFilter(field_name='organisation__id')
    chef_projet = django_filters.NumberFilter(field_name='chef_projet__id')
    date_debut_apres = django_filters.DateFilter(field_name='date_debut', lookup_expr='gte')
    date_fin_avant = django_filters.DateFilter(field_name='date_fin_prevue', lookup_expr='lte')
    en_retard = django_filters.BooleanFilter(method='filter_en_retard')

    class Meta:
        model = Projet
        fields = ['statut', 'priorite', 'programme', 'organisation', 'chef_projet']

    def filter_en_retard(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(
                statut='en_cours',
                date_fin_prevue__lt=timezone.now().date(),
            )
        return queryset


class RisqueFilter(django_filters.FilterSet):
    niveau_risque = django_filters.CharFilter(lookup_expr='exact')
    categorie = django_filters.ChoiceFilter(choices=RisqueProjet.CATEGORIE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=RisqueProjet.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')

    class Meta:
        model = RisqueProjet
        fields = ['niveau_risque', 'categorie', 'statut', 'projet']
