import django_filters
from .models import SessionTerrain, CollecteTerrain, PointageTerrain


class SessionTerrainFilter(django_filters.FilterSet):
    agent = django_filters.NumberFilter(field_name='agent__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    statut = django_filters.ChoiceFilter(choices=SessionTerrain.STATUT_CHOICES)
    mode_hors_ligne = django_filters.BooleanFilter()
    date_apres = django_filters.DateFilter(field_name='date_debut', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='date_debut', lookup_expr='date__lte')

    class Meta:
        model = SessionTerrain
        fields = ['agent', 'projet', 'statut', 'mode_hors_ligne']


class CollecteTerrainFilter(django_filters.FilterSet):
    session = django_filters.NumberFilter(field_name='session__id')
    type_collecte = django_filters.ChoiceFilter(choices=CollecteTerrain.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=CollecteTerrain.STATUT_CHOICES)
    indicateur = django_filters.NumberFilter(field_name='indicateur__id')
    formulaire = django_filters.NumberFilter(field_name='formulaire__id')
    agent = django_filters.NumberFilter(field_name='session__agent__id')
    projet = django_filters.NumberFilter(field_name='session__projet__id')
    date_apres = django_filters.DateFilter(field_name='date_collecte_locale', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='date_collecte_locale', lookup_expr='date__lte')

    class Meta:
        model = CollecteTerrain
        fields = ['session', 'type_collecte', 'statut', 'indicateur', 'formulaire']


class PointageTerrainFilter(django_filters.FilterSet):
    agent = django_filters.NumberFilter(field_name='agent__id')
    type_pointage = django_filters.ChoiceFilter(choices=PointageTerrain.TYPE_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    valide = django_filters.BooleanFilter()
    date_apres = django_filters.DateFilter(field_name='date_heure', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='date_heure', lookup_expr='date__lte')

    class Meta:
        model = PointageTerrain
        fields = ['agent', 'type_pointage', 'projet', 'valide']
