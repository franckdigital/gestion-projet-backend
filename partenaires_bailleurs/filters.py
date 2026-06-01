import django_filters
from django.utils import timezone
from .models import (
    Partenaire, ContactPartenaire, LiaisonProjetPartenaire,
    Convention, RenouvellementConvention,
    AccesPortailPartenaire, DepotDocumentPortail,
)


class PartenaireFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    sigle = django_filters.CharFilter(lookup_expr='icontains')
    type_partenaire = django_filters.ChoiceFilter(choices=Partenaire.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Partenaire.STATUT_CHOICES)
    pays = django_filters.CharFilter(lookup_expr='icontains')
    ville = django_filters.CharFilter(lookup_expr='icontains')
    avec_coordonnees = django_filters.BooleanFilter(
        method='filter_avec_coordonnees', label='Avec coordonnées GPS'
    )
    cree_par = django_filters.NumberFilter(field_name='cree_par__id')

    class Meta:
        model = Partenaire
        fields = ['type_partenaire', 'statut', 'pays']

    def filter_avec_coordonnees(self, queryset, name, value):
        if value:
            return queryset.filter(latitude__isnull=False, longitude__isnull=False)
        return queryset.filter(latitude__isnull=True)


class ContactPartenaireFilter(django_filters.FilterSet):
    partenaire = django_filters.NumberFilter(field_name='partenaire__id')
    role = django_filters.ChoiceFilter(choices=ContactPartenaire.ROLE_CHOICES)
    est_principal = django_filters.BooleanFilter()
    nom = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = ContactPartenaire
        fields = ['partenaire', 'role', 'est_principal']


class LiaisonProjetPartenaireFilter(django_filters.FilterSet):
    partenaire = django_filters.NumberFilter(field_name='partenaire__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    role = django_filters.ChoiceFilter(choices=LiaisonProjetPartenaire.ROLE_CHOICES)
    montant_min = django_filters.NumberFilter(field_name='montant_finance', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant_finance', lookup_expr='lte')

    class Meta:
        model = LiaisonProjetPartenaire
        fields = ['partenaire', 'projet', 'role']


class ConventionFilter(django_filters.FilterSet):
    intitule = django_filters.CharFilter(lookup_expr='icontains')
    reference = django_filters.CharFilter(lookup_expr='icontains')
    type_convention = django_filters.ChoiceFilter(choices=Convention.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Convention.STATUT_CHOICES)
    partenaire = django_filters.NumberFilter(field_name='partenaire__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    devise = django_filters.CharFilter(lookup_expr='iexact')
    montant_min = django_filters.NumberFilter(field_name='montant', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant', lookup_expr='lte')
    date_signature_apres = django_filters.DateFilter(field_name='date_signature', lookup_expr='gte')
    date_signature_avant = django_filters.DateFilter(field_name='date_signature', lookup_expr='lte')
    date_fin_avant = django_filters.DateFilter(field_name='date_fin', lookup_expr='lte')
    date_fin_apres = django_filters.DateFilter(field_name='date_fin', lookup_expr='gte')
    expirees = django_filters.BooleanFilter(method='filter_expirees', label='Conventions expirées')
    actives = django_filters.BooleanFilter(method='filter_actives', label='Conventions actives')

    class Meta:
        model = Convention
        fields = ['type_convention', 'statut', 'partenaire', 'programme', 'projet', 'devise']

    def filter_expirees(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(date_fin__lt=today)
        return queryset.filter(date_fin__gte=today)

    def filter_actives(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(statut__in=['actif', 'signe'], date_fin__gte=today)
        return queryset.exclude(statut__in=['actif', 'signe'])


class RenouvellementConventionFilter(django_filters.FilterSet):
    convention = django_filters.NumberFilter(field_name='convention__id')
    effectue_par = django_filters.NumberFilter(field_name='effectue_par__id')
    date_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = RenouvellementConvention
        fields = ['convention', 'effectue_par']


class AccesPortailPartenaireFilter(django_filters.FilterSet):
    partenaire = django_filters.NumberFilter(field_name='partenaire__id')
    utilisateur = django_filters.NumberFilter(field_name='utilisateur__id')
    niveau_acces = django_filters.ChoiceFilter(choices=AccesPortailPartenaire.NIVEAU_CHOICES)
    statut = django_filters.ChoiceFilter(choices=AccesPortailPartenaire.STATUT_CHOICES)
    accorde_par = django_filters.NumberFilter(field_name='accorde_par__id')

    class Meta:
        model = AccesPortailPartenaire
        fields = ['partenaire', 'utilisateur', 'niveau_acces', 'statut']


class DepotDocumentPortailFilter(django_filters.FilterSet):
    partenaire = django_filters.NumberFilter(field_name='partenaire__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    statut = django_filters.ChoiceFilter(choices=DepotDocumentPortail.STATUT_CHOICES)
    type_document = django_filters.CharFilter(lookup_expr='icontains')
    depose_par = django_filters.NumberFilter(field_name='depose_par__id')
    valide_par = django_filters.NumberFilter(field_name='valide_par__id')
    titre = django_filters.CharFilter(lookup_expr='icontains')
    date_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = DepotDocumentPortail
        fields = ['partenaire', 'projet', 'statut', 'depose_par']
