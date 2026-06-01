import django_filters
from .models import CourrierEntrant, CourrierSortant, Parapheur


class CourrierEntrantFilter(django_filters.FilterSet):
    urgence = django_filters.ChoiceFilter(choices=CourrierEntrant.URGENCE_CHOICES)
    canal = django_filters.ChoiceFilter(choices=CourrierEntrant.CANAL_CHOICES)
    statut = django_filters.ChoiceFilter(choices=CourrierEntrant.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    affecte_a = django_filters.NumberFilter(field_name='affecte_a__id')
    date_apres = django_filters.DateFilter(field_name='date_reception', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_reception', lookup_expr='lte')
    expediteur = django_filters.CharFilter(lookup_expr='icontains')
    objet = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = CourrierEntrant
        fields = ['urgence', 'canal', 'statut', 'projet', 'programme']


class CourrierSortantFilter(django_filters.FilterSet):
    type_courrier = django_filters.ChoiceFilter(choices=CourrierSortant.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=CourrierSortant.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    redacteur = django_filters.NumberFilter(field_name='redacteur__id')
    date_apres = django_filters.DateFilter(field_name='date_courrier', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_courrier', lookup_expr='lte')
    objet = django_filters.CharFilter(lookup_expr='icontains')
    destinataire = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = CourrierSortant
        fields = ['type_courrier', 'statut', 'projet', 'programme', 'redacteur']


class ParapheurFilter(django_filters.FilterSet):
    statut = django_filters.ChoiceFilter(choices=Parapheur.STATUT_CHOICES)
    soumis_par = django_filters.NumberFilter(field_name='soumis_par__id')
    circuit = django_filters.NumberFilter(field_name='circuit__id')

    class Meta:
        model = Parapheur
        fields = ['statut', 'soumis_par', 'circuit']
