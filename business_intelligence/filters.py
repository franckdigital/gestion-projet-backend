import django_filters
from .models import TableauBord, RapportBI, DataWarehouseSnapshot, DatamartFinance, DatamartSE


class TableauBordFilter(django_filters.FilterSet):
    type_dashboard = django_filters.ChoiceFilter(choices=TableauBord.TYPE_CHOICES)
    est_public = django_filters.BooleanFilter()
    est_defaut = django_filters.BooleanFilter()
    actif = django_filters.BooleanFilter()
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    proprietaire = django_filters.NumberFilter(field_name='proprietaire__id')

    class Meta:
        model = TableauBord
        fields = ['type_dashboard', 'est_public', 'est_defaut', 'actif', 'programme', 'projet']


class RapportBIFilter(django_filters.FilterSet):
    type_rapport = django_filters.ChoiceFilter(choices=RapportBI.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=RapportBI.STATUT_CHOICES)
    periode = django_filters.ChoiceFilter(choices=RapportBI.PERIODE_CHOICES)
    format_export = django_filters.ChoiceFilter(choices=RapportBI.FORMAT_CHOICES)
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    genere_par_ia = django_filters.BooleanFilter()
    date_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')

    class Meta:
        model = RapportBI
        fields = ['type_rapport', 'statut', 'periode', 'programme', 'projet', 'genere_par_ia']


class DatamartFinanceFilter(django_filters.FilterSet):
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    annee = django_filters.NumberFilter()
    mois = django_filters.NumberFilter()
    trimestre = django_filters.NumberFilter()
    bailleur = django_filters.CharFilter(lookup_expr='icontains')
    zone = django_filters.CharFilter(field_name='zone_geographique', lookup_expr='icontains')

    class Meta:
        model = DatamartFinance
        fields = ['programme', 'projet', 'annee', 'mois', 'trimestre']


class DatamartSEFilter(django_filters.FilterSet):
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    annee = django_filters.NumberFilter()
    trimestre = django_filters.NumberFilter()
    zone = django_filters.CharFilter(field_name='zone_geographique', lookup_expr='icontains')

    class Meta:
        model = DatamartSE
        fields = ['programme', 'projet', 'annee', 'trimestre']
