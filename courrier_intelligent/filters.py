import django_filters
from .models import Email


class EmailFilter(django_filters.FilterSet):
    direction = django_filters.ChoiceFilter(choices=Email.DIRECTION_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Email.STATUT_CHOICES)
    priorite = django_filters.ChoiceFilter(choices=Email.PRIORITE_CHOICES)
    est_lu = django_filters.BooleanFilter()
    traite_par_ia = django_filters.BooleanFilter()
    archive_ged = django_filters.BooleanFilter()
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    compte = django_filters.NumberFilter(field_name='compte__id')
    date_apres = django_filters.DateFilter(field_name='date_reception', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='date_reception', lookup_expr='date__lte')
    expediteur = django_filters.CharFilter(lookup_expr='icontains')
    sujet = django_filters.CharFilter(lookup_expr='icontains')
    etiquette = django_filters.NumberFilter(field_name='etiquettes__id')
    thread_id = django_filters.CharFilter(lookup_expr='exact')

    class Meta:
        model = Email
        fields = ['direction', 'statut', 'priorite', 'est_lu', 'projet', 'programme', 'etiquette', 'thread_id']
