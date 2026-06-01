import django_filters
from .models import ZoneSIG, CoucheCartographique, PointCartographie, InfrastructureSIG, CarteSIG


class ZoneSIGFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')
    type_zone = django_filters.ChoiceFilter(choices=ZoneSIG.TYPE_CHOICES)
    pays = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.NumberFilter(field_name='parent__id')
    sans_parent = django_filters.BooleanFilter(field_name='parent', lookup_expr='isnull')
    actif = django_filters.BooleanFilter()
    superficie_min = django_filters.NumberFilter(field_name='superficie_km2', lookup_expr='gte')
    superficie_max = django_filters.NumberFilter(field_name='superficie_km2', lookup_expr='lte')
    population_min = django_filters.NumberFilter(field_name='population', lookup_expr='gte')
    population_max = django_filters.NumberFilter(field_name='population', lookup_expr='lte')

    class Meta:
        model = ZoneSIG
        fields = ['type_zone', 'pays', 'actif', 'parent']


class CoucheCartographiqueFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    type_couche = django_filters.ChoiceFilter(choices=CoucheCartographique.TYPE_CHOICES)
    style_affichage = django_filters.ChoiceFilter(choices=CoucheCartographique.STYLE_CHOICES)
    est_visible = django_filters.BooleanFilter()
    est_publique = django_filters.BooleanFilter()
    filtre_programme = django_filters.NumberFilter(field_name='filtre_programme__id')
    filtre_projet = django_filters.NumberFilter(field_name='filtre_projet__id')
    cree_par = django_filters.NumberFilter(field_name='cree_par__id')

    class Meta:
        model = CoucheCartographique
        fields = ['type_couche', 'style_affichage', 'est_visible', 'est_publique']


class PointCartographieFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    type_point = django_filters.ChoiceFilter(choices=PointCartographie.TYPE_CHOICES)
    couche = django_filters.NumberFilter(field_name='couche__id')
    zone = django_filters.NumberFilter(field_name='zone__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    actif = django_filters.BooleanFilter()
    cree_par = django_filters.NumberFilter(field_name='cree_par__id')
    # Filtres géographiques (bounding box)
    lat_min = django_filters.NumberFilter(field_name='latitude', lookup_expr='gte')
    lat_max = django_filters.NumberFilter(field_name='latitude', lookup_expr='lte')
    lon_min = django_filters.NumberFilter(field_name='longitude', lookup_expr='gte')
    lon_max = django_filters.NumberFilter(field_name='longitude', lookup_expr='lte')

    class Meta:
        model = PointCartographie
        fields = ['type_point', 'couche', 'zone', 'programme', 'projet', 'actif']


class InfrastructureSIGFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    type_infrastructure = django_filters.ChoiceFilter(choices=InfrastructureSIG.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=InfrastructureSIG.STATUT_CHOICES)
    zone = django_filters.NumberFilter(field_name='zone__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    cree_par = django_filters.NumberFilter(field_name='cree_par__id')
    date_mise_en_service_apres = django_filters.DateFilter(
        field_name='date_mise_en_service', lookup_expr='gte')
    date_mise_en_service_avant = django_filters.DateFilter(
        field_name='date_mise_en_service', lookup_expr='lte')
    cout_min = django_filters.NumberFilter(field_name='cout_realisation', lookup_expr='gte')
    cout_max = django_filters.NumberFilter(field_name='cout_realisation', lookup_expr='lte')
    population_min = django_filters.NumberFilter(field_name='population_beneficiaire', lookup_expr='gte')
    # Filtres géographiques (bounding box)
    lat_min = django_filters.NumberFilter(field_name='latitude', lookup_expr='gte')
    lat_max = django_filters.NumberFilter(field_name='latitude', lookup_expr='lte')
    lon_min = django_filters.NumberFilter(field_name='longitude', lookup_expr='gte')
    lon_max = django_filters.NumberFilter(field_name='longitude', lookup_expr='lte')

    class Meta:
        model = InfrastructureSIG
        fields = ['type_infrastructure', 'statut', 'zone', 'programme', 'projet']


class CarteSIGFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    est_publique = django_filters.BooleanFilter()
    est_defaut = django_filters.BooleanFilter()
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    cree_par = django_filters.NumberFilter(field_name='cree_par__id')

    class Meta:
        model = CarteSIG
        fields = ['est_publique', 'est_defaut', 'programme', 'projet']
