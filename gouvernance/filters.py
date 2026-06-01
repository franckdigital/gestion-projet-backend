import django_filters
from .models import Organisation, Direction, Service, Site, Partenaire, Bailleur


class OrganisationFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    type_organisation = django_filters.ChoiceFilter(choices=Organisation.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Organisation.STATUT_CHOICES)
    pays = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Organisation
        fields = ['nom', 'type_organisation', 'statut', 'pays']


class DirectionFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    organisation = django_filters.NumberFilter(field_name='organisation__id')
    actif = django_filters.BooleanFilter()

    class Meta:
        model = Direction
        fields = ['organisation', 'actif']


class ServiceFilter(django_filters.FilterSet):
    intitule = django_filters.CharFilter(lookup_expr='icontains')
    direction = django_filters.NumberFilter(field_name='direction__id')
    organisation = django_filters.NumberFilter(field_name='direction__organisation__id')
    actif = django_filters.BooleanFilter()

    class Meta:
        model = Service
        fields = ['direction', 'actif']


class SiteFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    organisation = django_filters.NumberFilter(field_name='organisation__id')
    type_site = django_filters.ChoiceFilter(choices=Site.TYPE_CHOICES)
    ville = django_filters.CharFilter(lookup_expr='icontains')
    actif = django_filters.BooleanFilter()

    class Meta:
        model = Site
        fields = ['organisation', 'type_site', 'actif']


class PartenaireFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    type_partenaire = django_filters.ChoiceFilter(choices=Partenaire.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Partenaire.STATUT_CHOICES)
    pays = django_filters.CharFilter(lookup_expr='icontains')
    organisation = django_filters.NumberFilter(field_name='organisation__id')

    class Meta:
        model = Partenaire
        fields = ['type_partenaire', 'statut', 'organisation']


class BailleurFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    type_bailleur = django_filters.ChoiceFilter(choices=Bailleur.TYPE_CHOICES)
    pays_origine = django_filters.CharFilter(lookup_expr='icontains')
    organisation = django_filters.NumberFilter(field_name='organisation__id')
    actif = django_filters.BooleanFilter()

    class Meta:
        model = Bailleur
        fields = ['type_bailleur', 'organisation', 'actif']
